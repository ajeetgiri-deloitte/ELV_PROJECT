from decimal import Decimal
from django.db.models import Sum
from .models import *
import re
from datetime import timedelta
from django.utils import timezone


def is_valid_gst(gst_number: str) -> bool:

    if not gst_number:
        return False

    gst_number = gst_number.strip().upper()

    gst_pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][A-Z0-9][Z][A-Z0-9]$'

    return bool(re.match(gst_pattern, gst_number))

def calculate_steel_recovery_data(user_id):
    """
    Complete Steel Recovery Business Logic

    Includes:
    - Recovered & Processed validation
    - Fixed 2:1 ratio rule
    - Category-wise restriction
    - Subtract already sold steel
    """
    breakpoint
    # ---------------------------------------
    # 1️⃣ Total Other Scrap Recovered
    # ---------------------------------------
    total_other_scrap_recovered = (
        OtherScrap.objects
        .filter(rvsf_id=user_id)
        .aggregate(total=Sum("quantity"))
    )["total"] or Decimal("0")

    # ---------------------------------------
    # 2️⃣ Total Other Scrap Processed
    # ---------------------------------------
    total_other_scrap_processed = (
        WasteProcessing.objects
        .filter(rvsf_id=user_id)
        .aggregate(total=Sum("processed_qty"))
    )["total"] or Decimal("0")

    # ---------------------------------------
    # 3️⃣ HARD VALIDATION
    # ---------------------------------------
    if total_other_scrap_processed > total_other_scrap_recovered:
        raise ValueError(
            "Processed other scrap exceeds recovered quantity."
        )
    # breakpoint()
    # ---------------------------------------
    # 4️⃣ Fixed 2:1 Ratio
    # ---------------------------------------
    steel_allowed_from_ratio = total_other_scrap_processed * Decimal("2")

    # ---------------------------------------
    # 5️⃣ Steel Recovery Category Logic
    # ---------------------------------------

    # Category 1 (No restriction)
    qtySteelRecovered_cat1 = (
        ProductionForm.objects
        .filter(rvsf_id=user_id, category_id=2)
        .aggregate(total=Sum("steel_scrap_recovered"))
    )["total"] or Decimal("0")

    # Category 2 (Restricted category)
    actual_steel_cat2 = (
        ProductionForm.objects
        .filter(rvsf_id=user_id, category_id=1)
        .aggregate(total=Sum("steel_scrap_recovered"))
    )["total"] or Decimal("0")

    # ---------------------------------------
    # 6️⃣ Subtract Already Sold Steel
    # ---------------------------------------
    steel_scrap_sold = (
        SteelScrapSale.objects
        .filter(rvsf_id=user_id)
        .aggregate(total=Sum("quantity_sold"))
    )["total"] or Decimal("0")

    # Only subtract from category 2 stock
    available_cat2_after_sale = max(
        actual_steel_cat2 - max(steel_scrap_sold - qtySteelRecovered_cat1, Decimal("0")),
        Decimal("0")
    )
    

    # ---------------------------------------
    # 7️⃣ Apply Ratio Restriction
    # ---------------------------------------
    qtySteelRecovered_cat2 = min(
        available_cat2_after_sale,
        steel_allowed_from_ratio
    )

    # ---------------------------------------
    # 8️⃣ Final Total Steel Recovered
    # ---------------------------------------
    qtySteelRecovered = (
        qtySteelRecovered_cat1 + qtySteelRecovered_cat2
    )

    return {
        "total_other_scrap_recovered": total_other_scrap_recovered,
        "total_other_scrap_processed": total_other_scrap_processed,
        "steel_allowed_from_ratio": steel_allowed_from_ratio,
        "qtySteelRecovered_cat1": qtySteelRecovered_cat1,
        "actual_steel_cat2": actual_steel_cat2,
        "steel_scrap_sold": steel_scrap_sold,
        "qtySteelRecovered_cat2": qtySteelRecovered_cat2,
        "qtySteelRecovered": qtySteelRecovered,
    }    
    




def check_upload_limit(model, user_id, limit=5, minutes=10):
    """
    Generic upload rate limit checker.
    """

    time_threshold = timezone.now() - timedelta(minutes=minutes)

    count = model.objects.filter(
        rvsf_id=user_id,
        created_at__gte=time_threshold
    ).count()

    if count >= limit:
        return False

    return True

  