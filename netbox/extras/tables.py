import django_tables2 as tables
from django.conf import settings

from utilities.tables import (
    BaseTable, BooleanColumn, ButtonsColumn, ChoiceFieldColumn, ColorColumn, ContentTypeColumn, ContentTypesColumn,
    MarkdownColumn, ToggleColumn,
)
from .models import *

__all__ = (
    'ConfigContextTable',
    'CustomFieldTable',
    'CustomLinkTable',
    'ExportTemplateTable',
    'JournalEntryTable',
    'ObjectChangeTable',
    'ObjectJournalTable',
    'TaggedItemTable',
    'TagTable',
    'WebhookTable',
)

CONFIGCONTEXT_ACTIONS = """
{% if perms.extras.change_configcontext %}
    <a href="{% url 'extras:configcontext_edit' pk=record.pk %}" class="btn btn-sm btn-warning"><i class="mdi mdi-pencil" aria-hidden="true"></i></a>
{% endif %}
{% if perms.extras.delete_configcontext %}
    <a href="{% url 'extras:configcontext_delete' pk=record.pk %}" class="btn btn-sm btn-danger"><i class="mdi mdi-trash-can-outline" aria-hidden="true"></i></a>
{% endif %}
"""

OBJECTCHANGE_OBJECT = """
{% if record.changed_object.get_absolute_url %}
    <a href="{{ record.changed_object.get_absolute_url }}">{{ record.object_repr }}</a>
{% else %}
    {{ record.object_repr }}
{% endif %}
"""

OBJECTCHANGE_REQUEST_ID = """
<a href="{% url 'extras:objectchange_list' %}?request_id={{ value }}">{{ value }}</a>
"""


#
# Custom fields
#

class CustomFieldTable(BaseTable):
    pk = ToggleColumn()
    name = tables.Column(
        linkify=True
    )
    content_types = ContentTypesColumn()
    required = BooleanColumn()

    class Meta(BaseTable.Meta):
        model = CustomField
        fields = (
            'pk', 'id', 'name', 'content_types', 'label', 'type', 'required', 'weight', 'default',
            'description', 'filter_logic', 'choices',
        )
        default_columns = ('pk', 'name', 'content_types', 'label', 'type', 'required', 'description')


#
# Custom links
#

class CustomLinkTable(BaseTable):
    pk = ToggleColumn()
    name = tables.Column(
        linkify=True
    )
    content_type = ContentTypeColumn()
    new_window = BooleanColumn()

    class Meta(BaseTable.Meta):
        model = CustomLink
        fields = (
            'pk', 'id', 'name', 'content_type', 'link_text', 'link_url', 'weight', 'group_name',
            'button_class', 'new_window',
        )
        default_columns = ('pk', 'name', 'content_type', 'group_name', 'button_class', 'new_window')


#
# Export templates
#

class ExportTemplateTable(BaseTable):
    pk = ToggleColumn()
    name = tables.Column(
        linkify=True
    )
    content_type = ContentTypeColumn()
    as_attachment = BooleanColumn()

    class Meta(BaseTable.Meta):
        model = ExportTemplate
        fields = (
            'pk', 'id', 'name', 'content_type', 'description', 'mime_type', 'file_extension', 'as_attachment',
        )
        default_columns = (
            'pk', 'name', 'content_type', 'description', 'mime_type', 'file_extension', 'as_attachment',
        )


#
# Webhooks
#

class WebhookTable(BaseTable):
    pk = ToggleColumn()
    name = tables.Column(
        linkify=True
    )
    content_types = ContentTypesColumn()
    enabled = BooleanColumn()
    type_create = BooleanColumn(
        verbose_name='Create'
    )
    type_update = BooleanColumn(
        verbose_name='Update'
    )
    type_delete = BooleanColumn(
        verbose_name='Delete'
    )
    ssl_validation = BooleanColumn(
        verbose_name='SSL Validation'
    )

    class Meta(BaseTable.Meta):
        model = Webhook
        fields = (
            'pk', 'id', 'name', 'content_types', 'enabled', 'type_create', 'type_update', 'type_delete', 'http_method',
            'payload_url', 'secret', 'ssl_validation', 'ca_file_path',
        )
        default_columns = (
            'pk', 'name', 'content_types', 'enabled', 'type_create', 'type_update', 'type_delete', 'http_method',
            'payload_url',
        )


#
# Tags
#

class TagTable(BaseTable):
    pk = ToggleColumn()
    name = tables.Column(
        linkify=True
    )
    color = ColorColumn()
    actions = ButtonsColumn(Tag)

    class Meta(BaseTable.Meta):
        model = Tag
        fields = ('pk', 'id', 'name', 'items', 'slug', 'color', 'description', 'actions')
        default_columns = ('pk', 'name', 'items', 'slug', 'color', 'description', 'actions')


class TaggedItemTable(BaseTable):
    id = tables.Column(
        verbose_name='ID',
        linkify=lambda record: record.content_object.get_absolute_url(),
        accessor='content_object__id'
    )
    content_type = ContentTypeColumn(
        verbose_name='Type'
    )
    content_object = tables.Column(
        linkify=True,
        orderable=False,
        verbose_name='Object'
    )

    class Meta(BaseTable.Meta):
        model = TaggedItem
        fields = ('id', 'content_type', 'content_object')


class ConfigContextTable(BaseTable):
    pk = ToggleColumn()
    name = tables.Column(
        linkify=True
    )
    is_active = BooleanColumn(
        verbose_name='Active'
    )

    class Meta(BaseTable.Meta):
        model = ConfigContext
        fields = (
            'pk', 'id', 'name', 'weight', 'is_active', 'description', 'regions', 'sites', 'roles',
            'platforms', 'cluster_groups', 'clusters', 'tenant_groups', 'tenants',
        )
        default_columns = ('pk', 'name', 'weight', 'is_active', 'description')


class ObjectChangeTable(BaseTable):
    time = tables.DateTimeColumn(
        linkify=True,
        format=settings.SHORT_DATETIME_FORMAT
    )
    action = ChoiceFieldColumn()
    changed_object_type = ContentTypeColumn(
        verbose_name='Type'
    )
    object_repr = tables.TemplateColumn(
        template_code=OBJECTCHANGE_OBJECT,
        verbose_name='Object'
    )
    request_id = tables.TemplateColumn(
        template_code=OBJECTCHANGE_REQUEST_ID,
        verbose_name='Request ID'
    )

    class Meta(BaseTable.Meta):
        model = ObjectChange
        fields = ('id', 'time', 'user_name', 'action', 'changed_object_type', 'object_repr', 'request_id')


class ObjectJournalTable(BaseTable):
    """
    Used for displaying a set of JournalEntries within the context of a single object.
    """
    created = tables.DateTimeColumn(
        linkify=True,
        format=settings.SHORT_DATETIME_FORMAT
    )
    kind = ChoiceFieldColumn()
    comments = tables.TemplateColumn(
        template_code='{% load helpers %}{{ value|render_markdown|truncatewords_html:50 }}'
    )
    actions = ButtonsColumn(
        model=JournalEntry
    )

    class Meta(BaseTable.Meta):
        model = JournalEntry
        fields = ('id', 'created', 'created_by', 'kind', 'comments', 'actions')


class JournalEntryTable(ObjectJournalTable):
    pk = ToggleColumn()
    assigned_object_type = ContentTypeColumn(
        verbose_name='Object type'
    )
    assigned_object = tables.Column(
        linkify=True,
        orderable=False,
        verbose_name='Object'
    )
    comments = MarkdownColumn()

    class Meta(BaseTable.Meta):
        model = JournalEntry
        fields = (
            'pk', 'id', 'created', 'created_by', 'assigned_object_type', 'assigned_object', 'kind',
            'comments', 'actions'
        )
        default_columns = (
            'pk', 'created', 'created_by', 'assigned_object_type', 'assigned_object', 'kind',
            'comments', 'actions'
        )
