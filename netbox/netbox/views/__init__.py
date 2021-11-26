import platform
import sys

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models import F
from django.http import HttpResponseServerError
from django.shortcuts import redirect, render
from django.template import loader
from django.template.exceptions import TemplateDoesNotExist
from django.urls import reverse
from django.views.decorators.csrf import requires_csrf_token
from django.views.defaults import ERROR_500_TEMPLATE_NAME
from django.views.generic import View
from packaging import version

from circuits.models import Circuit, Provider
from dcim.models import (
    Cable, ConsolePort, Device, DeviceType, Interface, PowerPanel, PowerFeed, PowerPort, Rack, Site,
)
from extras.choices import JobResultStatusChoices
from extras.models import ObjectChange, JobResult
from extras.tables import ObjectChangeTable
from ipam.models import Aggregate, IPAddress, IPRange, Prefix, VLAN, VRF
from netbox.constants import SEARCH_MAX_RESULTS, SEARCH_TYPES
from netbox.forms import SearchForm
from tenancy.models import Tenant
from virtualization.models import Cluster, VirtualMachine


class HomeView(View):
    template_name = 'home.html'

    def get(self, request):
        if settings.LOGIN_REQUIRED and not request.user.is_authenticated:
            return redirect("login")

        connected_consoleports = ConsolePort.objects.restrict(request.user, 'view').prefetch_related('_path').filter(
            _path__destination_id__isnull=False
        )
        connected_powerports = PowerPort.objects.restrict(request.user, 'view').prefetch_related('_path').filter(
            _path__destination_id__isnull=False
        )
        connected_interfaces = Interface.objects.restrict(request.user, 'view').prefetch_related('_path').filter(
            _path__destination_id__isnull=False,
            pk__lt=F('_path__destination_id')
        )

        # Report Results
        report_content_type = ContentType.objects.get(app_label='extras', model='report')
        report_results = JobResult.objects.filter(
            obj_type=report_content_type,
            status__in=JobResultStatusChoices.TERMINAL_STATE_CHOICES
        ).defer('data')[:10]

        def build_stats():
            org = (
                ("dcim.view_site", "Sites", Site.objects.restrict(request.user, 'view').count),
                ("tenancy.view_tenant", "Tenants", Tenant.objects.restrict(request.user, 'view').count),
            )
            dcim = (
                ("dcim.view_rack", "Racks", Rack.objects.restrict(request.user, 'view').count),
                ("dcim.view_devicetype", "Device Types", DeviceType.objects.restrict(request.user, 'view').count),
                ("dcim.view_device", "Devices", Device.objects.restrict(request.user, 'view').count),
            )
            ipam = (
                ("ipam.view_vrf", "VRFs", VRF.objects.restrict(request.user, 'view').count),
                ("ipam.view_aggregate", "Aggregates", Aggregate.objects.restrict(request.user, 'view').count),
                ("ipam.view_prefix", "Prefixes", Prefix.objects.restrict(request.user, 'view').count),
                ("ipam.view_iprange", "IP Ranges", IPRange.objects.restrict(request.user, 'view').count),
                ("ipam.view_ipaddress", "IP Addresses", IPAddress.objects.restrict(request.user, 'view').count),
                ("ipam.view_vlan", "VLANs", VLAN.objects.restrict(request.user, 'view').count)

            )
            circuits = (
                ("circuits.view_provider", "Providers", Provider.objects.restrict(request.user, 'view').count),
                ("circuits.view_circuit", "Circuits", Circuit.objects.restrict(request.user, 'view').count),
            )
            virtualization = (
                ("virtualization.view_cluster", "Clusters", Cluster.objects.restrict(request.user, 'view').count),
                ("virtualization.view_virtualmachine", "Virtual Machines", VirtualMachine.objects.restrict(request.user, 'view').count),

            )
            connections = (
                ("dcim.view_cable", "Cables", Cable.objects.restrict(request.user, 'view').count),
                ("dcim.view_consoleport", "Console", connected_consoleports.count),
                ("dcim.view_interface", "Interfaces", connected_interfaces.count),
                ("dcim.view_powerport", "Power Connections", connected_powerports.count),
            )
            power = (
                ("dcim.view_powerpanel", "Power Panels", PowerPanel.objects.restrict(request.user, 'view').count),
                ("dcim.view_powerfeed", "Power Feeds", PowerFeed.objects.restrict(request.user, 'view').count),
            )
            sections = (
                ("Organization", org, "domain"),
                ("IPAM", ipam, "counter"),
                ("Virtualization", virtualization, "monitor"),
                ("Inventory", dcim, "server"),
                ("Connections", connections, "cable-data"),
                ("Circuits", circuits, "transit-connection-variant"),
                ("Power", power, "flash"),
            )

            stats = []
            for section_label, section_items, icon_class in sections:
                items = []
                for perm, item_label, get_count in section_items:
                    app, scope = perm.split(".")
                    url = ":".join((app, scope.replace("view_", "") + "_list"))
                    item = {
                        "label": item_label,
                        "count": None,
                        "url": url,
                        "disabled": True,
                        "icon": icon_class,
                    }
                    if request.user.has_perm(perm):
                        item["count"] = get_count()
                        item["disabled"] = False
                    items.append(item)
                stats.append((section_label, items, icon_class))

            return stats

        # Compile changelog table
        changelog = ObjectChange.objects.restrict(request.user, 'view').prefetch_related(
            'user', 'changed_object_type'
        )[:10]
        changelog_table = ObjectChangeTable(changelog)

        # Check whether a new release is available. (Only for staff/superusers.)
        new_release = None
        if request.user.is_staff or request.user.is_superuser:
            latest_release = cache.get('latest_release')
            if latest_release:
                release_version, release_url = latest_release
                if release_version > version.parse(settings.VERSION):
                    new_release = {
                        'version': str(release_version),
                        'url': release_url,
                    }

        return render(request, self.template_name, {
            'search_form': SearchForm(),
            'stats': build_stats(),
            'report_results': report_results,
            'changelog_table': changelog_table,
            'new_release': new_release,
        })


class SearchView(View):

    def get(self, request):
        form = SearchForm(request.GET)
        results = []

        if form.is_valid():

            # If an object type has been specified, redirect to the dedicated view for it
            if form.cleaned_data['obj_type']:
                object_type = form.cleaned_data['obj_type']
                url = reverse(SEARCH_TYPES[object_type]['url'])
                return redirect(f"{url}?q={form.cleaned_data['q']}")

            for obj_type in SEARCH_TYPES.keys():

                queryset = SEARCH_TYPES[obj_type]['queryset'].restrict(request.user, 'view')
                filterset = SEARCH_TYPES[obj_type]['filterset']
                table = SEARCH_TYPES[obj_type]['table']
                url = SEARCH_TYPES[obj_type]['url']

                # Construct the results table for this object type
                filtered_queryset = filterset({'q': form.cleaned_data['q']}, queryset=queryset).qs
                table = table(filtered_queryset, orderable=False)
                table.paginate(per_page=SEARCH_MAX_RESULTS)

                if table.page:
                    results.append({
                        'name': queryset.model._meta.verbose_name_plural,
                        'table': table,
                        'url': f"{reverse(url)}?q={form.cleaned_data.get('q')}"
                    })

        return render(request, 'search.html', {
            'form': form,
            'results': results,
        })


class StaticMediaFailureView(View):
    """
    Display a user-friendly error message with troubleshooting tips when a static media file fails to load.
    """

    def get(self, request):
        return render(request, 'media_failure.html', {
            'filename': request.GET.get('filename')
        })


@requires_csrf_token
def server_error(request, template_name=ERROR_500_TEMPLATE_NAME):
    """
    Custom 500 handler to provide additional context when rendering 500.html.
    """
    try:
        template = loader.get_template(template_name)
    except TemplateDoesNotExist:
        return HttpResponseServerError('<h1>Server Error (500)</h1>', content_type='text/html')
    type_, error, traceback = sys.exc_info()

    return HttpResponseServerError(template.render({
        'error': error,
        'exception': str(type_),
        'netbox_version': settings.VERSION,
        'python_version': platform.python_version(),
    }))
