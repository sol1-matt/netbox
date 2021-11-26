import django_tables2 as tables
from django_tables2.utils import Accessor

from dcim.models import Rack, RackReservation, RackRole
from tenancy.tables import TenantColumn
from utilities.tables import (
    BaseTable, ButtonsColumn, ChoiceFieldColumn, ColorColumn, ColoredLabelColumn, LinkedCountColumn, MarkdownColumn,
    TagColumn, ToggleColumn, UtilizationColumn,
)

__all__ = (
    'RackTable',
    'RackReservationTable',
    'RackRoleTable',
)


#
# Rack roles
#

class RackRoleTable(BaseTable):
    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    rack_count = tables.Column(verbose_name='Racks')
    color = ColorColumn()
    actions = ButtonsColumn(RackRole)

    class Meta(BaseTable.Meta):
        model = RackRole
        fields = ('pk', 'id', 'name', 'rack_count', 'color', 'description', 'slug', 'actions')
        default_columns = ('pk', 'name', 'rack_count', 'color', 'description', 'actions')


#
# Racks
#

class RackTable(BaseTable):
    pk = ToggleColumn()
    name = tables.Column(
        order_by=('_name',),
        linkify=True
    )
    location = tables.Column(
        linkify=True
    )
    site = tables.Column(
        linkify=True
    )
    tenant = TenantColumn()
    status = ChoiceFieldColumn()
    role = ColoredLabelColumn()
    u_height = tables.TemplateColumn(
        template_code="{{ record.u_height }}U",
        verbose_name='Height'
    )
    comments = MarkdownColumn()
    device_count = LinkedCountColumn(
        viewname='dcim:device_list',
        url_params={'rack_id': 'pk'},
        verbose_name='Devices'
    )
    get_utilization = UtilizationColumn(
        orderable=False,
        verbose_name='Space'
    )
    get_power_utilization = UtilizationColumn(
        orderable=False,
        verbose_name='Power'
    )
    tags = TagColumn(
        url_name='dcim:rack_list'
    )
    outer_width = tables.TemplateColumn(
        template_code="{{ record.outer_width }} {{ record.outer_unit }}",
        verbose_name='Outer Width'
    )
    outer_depth = tables.TemplateColumn(
        template_code="{{ record.outer_depth }} {{ record.outer_unit }}",
        verbose_name='Outer Depth'
    )

    class Meta(BaseTable.Meta):
        model = Rack
        fields = (
            'pk', 'id', 'name', 'site', 'location', 'status', 'facility_id', 'tenant', 'role', 'serial', 'asset_tag', 'type',
            'width', 'outer_width', 'outer_depth', 'u_height', 'comments', 'device_count', 'get_utilization', 'get_power_utilization', 'tags',
        )
        default_columns = (
            'pk', 'name', 'site', 'location', 'status', 'facility_id', 'tenant', 'role', 'u_height', 'device_count',
            'get_utilization', 'get_power_utilization',
        )


#
# Rack reservations
#

class RackReservationTable(BaseTable):
    pk = ToggleColumn()
    reservation = tables.Column(
        accessor='pk',
        linkify=True
    )
    site = tables.Column(
        accessor=Accessor('rack__site'),
        linkify=True
    )
    tenant = TenantColumn()
    rack = tables.Column(
        linkify=True
    )
    unit_list = tables.Column(
        orderable=False,
        verbose_name='Units'
    )
    tags = TagColumn(
        url_name='dcim:rackreservation_list'
    )
    actions = ButtonsColumn(RackReservation)

    class Meta(BaseTable.Meta):
        model = RackReservation
        fields = (
            'pk', 'id', 'reservation', 'site', 'rack', 'unit_list', 'user', 'created', 'tenant', 'description', 'tags',
            'actions',
        )
        default_columns = (
            'pk', 'reservation', 'site', 'rack', 'unit_list', 'user', 'description', 'actions',
        )
