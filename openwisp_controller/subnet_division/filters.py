from django.contrib import admin
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from swapper import load_model

from . import settings as app_settings

SubnetDivisionIndex = load_model('subnet_division', 'SubnetDivisionIndex')
Subnet = load_model('openwisp_ipam', 'Subnet')


class InputFilter(admin.SimpleListFilter):
    template = 'admin/input_filter.html'

    def lookups(self, request, model_admin):
        # Required to show the filter.
        return [tuple()]

    def choices(self, changelist):
        # Grab only the "all" option.
        all_choice = next(super().choices(changelist))
        all_choice['query_parts'] = []
        for key, value in changelist.get_filters_params().items():
            if key != self.parameter_name:
                all_choice['query_parts'].append((key, value))
        yield all_choice


class SubnetFilter(InputFilter):
    parameter_name = 'subnet'
    title = _('subnet')

    def queryset(self, request, queryset):
        if self.value() is not None:
            master_subnet_key = (
                'config__subnetdivisionindex__subnet__master_subnet__subnet'
            )
            return queryset.filter(
                Q(**{master_subnet_key: self.value()})
                | Q(config__subnetdivisionindex__subnet__subnet=self.value())
            ).distinct()


class DeviceFilter(InputFilter):
    """
    Filters Subnet queryset for input device name
    using SubnetDivisionIndex
    """

    parameter_name = 'device'
    title = _('device name')

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(
                id__in=SubnetDivisionIndex.objects.filter(
                    config__device__name=self.value()
                ).values_list('subnet_id')
            )


class SubnetListFilter(admin.RelatedFieldListFilter):
    def field_choices(self, field, request, model_admin):
        if app_settings.HIDE_GENERATED_SUBNETS and field.name == 'subnet':
            return field.get_choices(
                include_blank=False,
                limit_choices_to={
                    'id__in': Subnet.objects.exclude(
                        id__in=SubnetDivisionIndex.objects.filter(
                            ip__isnull=True, subnet__isnull=False
                        ).values_list('subnet_id')
                    )
                },
            )
        choices = super().field_choices(field, request, model_admin)
        return choices
