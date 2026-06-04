from django import template
from django.core import signing

register = template.Library()

@register.filter(name='encrypt_id')
def encrypt_id(value):
    """Encrypt (sign) the given producer ID."""
    try:
        return signing.dumps(value)
    except Exception:
        return ''

@register.filter
def get_item(dictionary, key):
    try:
        return dictionary.get(int(key))
    except (ValueError, TypeError):
        return None

@register.filter
def get_checklist(dictionary, key):
    if not dictionary or not key:
        return None
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return getattr(dictionary, key, None)

@register.filter
def get_checklist_item(dictionary, key):
    value = dictionary.get(key)
    return value if value is not None else ""

@register.filter
def get_choices(form, field_name):
    try:
        return form.fields[field_name].choices
    except (KeyError, AttributeError):
        return []


@register.filter
def get_field_by_name(form, field_name):
    return form[field_name]

@register.filter
def add_20_years(fy_str):
    try:
        start, end = fy_str.split('-')
        new_start = int(start) + 20
        new_end = new_start + 1
        return f"{new_start}-{str(new_end)[-2:]}"
    except:
        return fy_str  
    

@register.filter
def add_15_years(fy_str):
    try:
        start, end = fy_str.split('-')
        new_start = int(start) + 15
        new_end = new_start + 1
        return f"{new_start}-{str(new_end)[-2:]}"
    except:
        return fy_str  

@register.filter
def dict_get(dict_obj, key):
    return dict_obj.get(key, {})

@register.filter
def dictkey(d, key):
    try:
        if d is None:
            return ''
        # try exact match first
        if key in d:
            return d[key]
        # fallback: string key
        return d.get(str(key), '')
    except Exception:
        return ''

# @register.filter
# def dictkey(d, key):
#     try:
#         return d.get(key, '')
#     except:
#         return ''
    
@register.filter
def attr(obj, attr_name):
    return getattr(obj, attr_name, '')



@register.filter
def has_any_no_transport(checklist):
    return any([
        checklist.data_transport == "no",
        checklist.fy_data_transport == "no",
        checklist.vehicle_data_transport == "no",
        checklist.manufactured_data_transport == "no",
        checklist.open_market_sales_data_transport == "no",
        checklist.other_producer_sales_data_transport == "no",
        checklist.cobranding_sales_data_transport == "no",
        checklist.uploaded_excel_other_producer_standard_format_transport == "no",
        checklist.self_use_transport == "no",
        checklist.exported_vehicles_transport == "no",
        checklist.uploaded_ca_certificates_each_fy_transport == "no",
    ])
    
@register.filter
def has_any_no_non_transport(checklist):
    return any([
        checklist.data_non_transport == "no",
        checklist.fy_data_non_transport == "no",
        checklist.vehicle_data_non_transport == "no",
        checklist.manufactured_data_non_transport == "no",
        checklist.open_market_sales_data_non_transport == "no",
        checklist.other_producer_sales_data_non_transport == "no",
        checklist.cobranding_sales_data_non_transport == "no",
        checklist.uploaded_excel_standard_format_non_transport == "no",
        checklist.self_use_non_transport == "no",
        checklist.exported_vehicles_non_transport == "no",
        checklist.uploaded_ca_certificates_each_fy_non_transport == "no",
    ])
    
    
@register.filter
def has_any_no(checklist):
    return any([
        checklist.manufactured_imported_procurement_year_wise == "no",
        checklist.sales_data_open_market_brand_name == "no",
        checklist.sales_data_other_producers_cobranding == "no",
        checklist.uploaded_excel_other_producer_standard_format == "no",
        checklist.details_exported_vehicles == "no",
        checklist.mfg_import_procure_yr_non_trans == "no",
        checklist.sold_open_market_brand_non_trans == "no",
        checklist.sold_other_prod_cobrand_non_trans == "no",
        checklist.uploaded_excel_sold_other_prod_non_trans == "no",
        checklist.details_exported_vehicles_non_trans == "no",
    ])
    
@register.simple_tag
def get_counter(counter):
    return counter + 1

@register.filter
def indian_currency(value):
    try:
        value = int(value)
        s = str(value)
        # First group (last 3 digits)
        last3 = s[-3:]
        rest = s[:-3]

        if rest != "":
            rest = rest[::-1]
            groups = [rest[i:i+2] for i in range(0, len(rest), 2)]
            rest = ",".join(groups)[::-1]
            return rest + "," + last3
        else:
            return last3
    except:
        return value
