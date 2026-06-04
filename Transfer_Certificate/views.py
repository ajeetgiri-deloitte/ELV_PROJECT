from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_date
import json
from decimal import Decimal
from registration.models import producerGeneralDetails, Registration
from RvsfApp.models import *
from .models import *
from .common_utils import *
import os
from PyPDF2 import PdfReader

# views.py
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, OuterRef, Subquery

from django.db import transaction
from django.utils.timezone import now
import random

from django.http import Http404, FileResponse
from django.conf import settings
import os,requests
from django.core.cache import cache
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64
from cryptography.hazmat.backends import default_backend

# ===============================
# 1. PROCUREMENT DETAILS
# ===============================

from datetime import date

def decrypt_aes_cert(encrypted_text):
    key = b"16charSecretKey!"  # same as client
    iv = b"16charSecretIV!!"   # same as client
    encrypted_bytes = base64.b64decode(encrypted_text)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_padded = decryptor.update(encrypted_bytes) + decryptor.finalize()
    # remove PKCS7 padding
    pad_len = decrypted_padded[-1]
    return decrypted_padded[:-pad_len].decode('utf-8')

def verify_otp_cert(request):
    userid = request.session.get('user_id')
    print("🔹 Entered verify_otp view")
    if request.method == 'POST':
        print("✅ Request method is POST")

        

        # ✅ Decrypt the OTP sent from client
        enc_otp = request.POST.get('enc_otp')
        print(enc_otp)
        print(f"🔒 Encrypted OTP received: {enc_otp}")

        try:
            entered_otp = decrypt_aes_cert(enc_otp)
            print(f"🔓 Decrypted OTP: {entered_otp}")
        except Exception as e:
            print(f"❌ OTP decryption failed: {e}")
            messages.error(request, "OTP decryption failed.")
            return  redirect('certificate_transfer_dashboard')

       
        # Step 2: Validate OTP
        user_number=RvsfRegistration.objects.filter(id=userid).first()
        print("🧩 Fetching stored OTP from cache...")
        stored_otp = cache.get(f"otp_{user_number.username}")
        print(enc_otp,stored_otp,'tops')
        print(f"📦 Stored OTP in cache: {stored_otp}")

        if stored_otp is None:
            print("⚠️ No OTP found or expired in cache")
            messages.error(request, 'OTP expired or not found. Please request a new one.')
            return  redirect('certificate_transfer_dashboard')

        if stored_otp != entered_otp:
            return JsonResponse({"status": "error", "message": "Invalid OTP"})

        cache.delete(f"otp_{user_number.username}")

        return JsonResponse({"status": "success"})


        # Step 3: OTP correct → proceed
        print("✅ OTP verified successfully. Deleting from cache...")
        cache.delete(f"otp_{user_number.username}")

        print("🔎 Fetching user record from database...")
                
        request.session['is_rvsf_logged_in'] = True
        print("🏠 Returning user — redirecting to dashboard")
        return redirect('certificate_transfer_dashboard')

    print("⚠️ Request method not POST — redirecting to home")
    return redirect('certificate_transfer_dashboard')

def send_sms_otp_for_transfer(request):
    if request.method == "POST":

        userid = request.session.get('user_id')
        user_number = RvsfRegistration.objects.filter(id=userid).first()

        # otp = str(random.randint(100000, 999999))
        otp = "123456"
        cache.set(f"otp_{user_number.username}", otp, timeout=120)
    # API credentials & configuration
    username = "CPCB_IT"
    password = "Cpcbsms#2020"
    senderid = "CPCBEL"
    dept_secure_key = "106a9ed9-00c4-442d-a857-3447d308c9d9"
    templateid = "1307175188771815034"
    entity_id = "1301158798803147760"

    # OTP message
    message = (
        f"Dear User, Your OTP for Transfer Certificate ELV EPR Portal is {otp}. Please enter this code to complete the Transfer Certificate Verification. Do not share this OTP with anyone. Regards, CPCB."
    )

    # Encrypt password
    encrypted_password = hashlib.sha1(password.strip().encode()).hexdigest()

    # Generate key for request
    key_string = f"{username.strip()}{senderid.strip()}{message.strip()}{dept_secure_key.strip()}"
    key = hashlib.sha512(key_string.encode()).hexdigest()

    # API payload
    payload = {
        "username": username.strip(),
        "password": encrypted_password,
        "senderid": senderid.strip(),
        "content": message.strip(),
        "smsservicetype": "singlemsg",
        "mobileno": user_number.auth_mobile.strip(),
        "key": key,
        "templateid": templateid.strip(),
        "entityid": entity_id.strip(),
    }

    try:
        # ✅ Send request to NEW API endpoint
        test_url = "https://msdgweb.mgov.gov.in/esms/sendsmsrequestDLT"
        response = requests.post(test_url, data=payload, timeout=10)

        print("API Raw Response (repr):", repr(response.text))
        print("Status code:", response.status_code)
        print("Request Payload Sent:", payload)
        print("API Response Code:", response.status_code)
        print("API Response Text:", response.text)

        return JsonResponse({"status": "success", "message": "OTP sent successfully"})

    except requests.RequestException as e:
        print("Failed to send OTP:", str(e))
        return JsonResponse({"status": "error"}, status=400)










def protected_cert_file(request, path):
    # Check for either admin or producer login
    # admin_id = request.session.get('admin_user_id')
    # rvsf_id = request.session.get('user_id')
    # user_role = request.session.get('user_role')
    # rvsf_id = 49
    rvsf_id = request.session.get('user_id')
    user_role = request.session.get('user_role')
    # user_role = 'rvsf'
    
    # if neither producer nor admin logged in
    if not rvsf_id:
        # Redirect based on role (default to producer login)
        if user_role == 'rvsf':
            return redirect('rvsf_home')  # use your producer login view name
        else:
            return redirect('custom_admin_login')

    # File access
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.exists(file_path):
        raise Http404("File not found")

    return FileResponse(open(file_path, 'rb'), as_attachment=False)



def get_current_financial_year():
    today = date.today()

    if today.month >= 4:
        return f"{today.year}-{today.year + 1}"
    else:
        return f"{today.year - 1}-{today.year}"
    

# def get_fy_from_date(date_obj):
#     if date_obj.month >= 4:  # April or later
#         return f"{date_obj.year}-{date_obj.year + 1}"
#     else:
#         return f"{date_obj.year - 1}-{date_obj.year}"

def get_fy_from_date(date_obj):
    """
    Accepts date / datetime object
    Returns FY in YYYY-YYYY format
    """
    if isinstance(date_obj, str):
        date_obj = datetime.strptime(date_obj, "%d-%m-%Y").date()

    if date_obj.month >= 4:  # April or later
        return f"{date_obj.year}-{date_obj.year + 1}"
    else:
        return f"{date_obj.year - 1}-{date_obj.year}"
    
    
def generate_fy_range(start_fy, end_fy):
    """
    start_fy, end_fy: 'YYYY-YYYY'
    """
    start_year = int(start_fy.split("-")[0])
    end_year = int(end_fy.split("-")[0])

    return [
        f"{y}-{y+1}" for y in range(start_year, end_year + 1)
    ]


def is_valid_pdf(uploaded_file, max_size_mb=2):
    try:
        max_bytes = max_size_mb * 1024 * 1024
        if uploaded_file.size > max_bytes:
            return False
        # 1️⃣ Single Extension Check

        filename = uploaded_file.name

        # Must contain only one dot before extension
        name, ext = os.path.splitext(filename)

        if ext.lower() != ".pdf":
            return False

        if "." in name:   # prevents file.pdf.exe or file.test.pdf
            return False

        # 2️⃣ Header Check
        uploaded_file.seek(0)
        if uploaded_file.read(5) != b'%PDF-':
            return False
        uploaded_file.seek(0)

        # 3️⃣ Structural Check
        reader = PdfReader(uploaded_file)
        if len(reader.pages) == 0:
            return False

        uploaded_file.seek(0)
        return True

    except Exception:
        return False
    
      
def opening_balance(request):
    print(dict(request.session))
    try:
        # TEMP login
        # rvsf_id = 49  # remove later
        rvsf_id = request.session.get('user_id')
        # user_role = request.session.get('user_role')
        user_role = request.session.get("user_role")
        is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

        if not rvsf_id or user_role != "rvsf" or not is_rvsf_logged_in:
            messages.error(request, "Unauthorized access.")
            return redirect("logoutrvsf")
        if not rvsf_id:
            messages.error(request, "RVSF not logged in")
            return redirect("login")

        rvsf = RvsfRegistration.objects.get(id=rvsf_id)

        # ------------------------------------
        # STEP 1: Determine allowed FY
        # ------------------------------------
        # incorp_fy = get_fy_from_date(rvsf.year_of_incorporation)
        incorp_fy = get_fy_from_date("01-05-2022")  # testing

        if incorp_fy < "2025-2026":
            fy_string = "2025-2026"
            financial_year_obj, created = FinancialYear.objects.get_or_create(
                rvsf=rvsf,
                financial_year=fy_string,
                defaults={"is_active": True},
            )
        else:
            fy_string = get_current_financial_year()
            financial_year_obj, created = FinancialYear.objects.get_or_create(
                rvsf=rvsf,
                financial_year=fy_string,
                defaults={"is_active": True},
            )
            return redirect("procurement_dashboard")

        
        
        # print(financial_year_obj)

        # ------------------------------------
        # STEP 3: Check if Opening Balance already submitted
        # ------------------------------------
        if OpeningBalance.objects.filter(
            financial_year=financial_year_obj
        ).exists():
            messages.info(
                request,
                "Opening balance already submitted for this financial year."
            )
            return redirect("procurement_dashboard")

        # ------------------------------------
        # STEP 4: Fetch ELV Types
        # ------------------------------------
        elv_types = VehicleType.objects.filter(userid=rvsf_id)

        # ------------------------------------
        # STEP 5: POST – Save Opening Balance
        # ------------------------------------
        if request.method == "POST":
            saved = False

            for t in elv_types:
                qty = request.POST.get(f"qty_{t.id}")

                if qty and int(qty) > 0:
                    OpeningBalance.objects.create(
                        financial_year=financial_year_obj,
                        elv_type=t.vehicle_type,
                        opening_balance_quantity=int(qty),
                    )
                    saved = True

            if not saved:
                messages.error(
                    request,
                    "Please enter opening balance for at least one ELV type."
                )
                return redirect("opening_balance")

            messages.success(
                request,
                "Opening balance saved successfully."
            )
            return redirect("procurement_dashboard")

        # ------------------------------------
        # STEP 6: Render Form
        # ------------------------------------
        return render(
            request,
            "procurement_detail/opening_balance_form.html",
            {
                "financial_year": fy_string,
                "elv_types": elv_types,
            },
        )

    except Exception as e:
        messages.error(request, "Something went wrong. Please try again.")
        return redirect("procurement_dashboard")

def procurement_dashboard(request):
    print(dict(request.session))
    # rvsf_id = 49  # remove later
    rvsf_id = request.session.get('user_id')
    # user_role = request.session.get('user_role')
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")
    print(request.session.get('user_id'),'dwqdajhah')

    if not rvsf_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not rvsf_id:
        return redirect("logoutrvsf")

    rvsf = RvsfRegistration.objects.get(id=rvsf_id)

    # ------------------------------------
    # STEP 1: Determine FY range
    # ------------------------------------
    incorp_fy = get_fy_from_date("01-05-2022")  # e.g. '2022-2023'
    current_fy = get_current_financial_year()  # e.g. '2025-2026'

    BASE_FY = "2025-2026"

    # Choose later FY (BASE_FY vs Incorporation FY)
    start_fy = (
        incorp_fy
        if int(incorp_fy.split("-")[0]) > int(BASE_FY.split("-")[0])
        else BASE_FY
    )

    # Generate FY dropdown list
    fy_list = generate_fy_range(start_fy, current_fy)

    # Selected FY
    selected_fy = request.GET.get("fy", current_fy)

    # -------------------------------
    # Financial Year object
    # -------------------------------
    fy_obj = FinancialYear.objects.filter(
        rvsf=rvsf_id,
        financial_year=selected_fy
    ).first()

    # -------------------------------
    # Opening Balance
    # -------------------------------
    opening_dict = {}

    if fy_obj:
        opening_balances = (
            OpeningBalance.objects
            .filter(financial_year=fy_obj)
            .values("elv_type")
            .annotate(opening_qty=Sum("opening_balance_quantity"))
        )
        opening_dict = {
            ob["elv_type"]: ob["opening_qty"]
            for ob in opening_balances
        }

    # -------------------------------
    # Procured ELVs
    # -------------------------------
    procured_data = (
        ProcurementData.objects
        .filter(rvsf_id=rvsf_id, financial_year=selected_fy, procurement_type='ELV')
        .values("vehicle_type")
        .annotate(procured_qty=Sum("number_of_elvs"))
    )

    procured_dict = {
        p["vehicle_type"]: p["procured_qty"]
        for p in procured_data
    }
    
    automobile_qty = (
        ProcurementData.objects
        .filter(
            rvsf_id=rvsf_id,
            financial_year=selected_fy,
            procurement_type="AUTOMOBILE"
        )
        .aggregate(total_qty=Sum("number_of_elvs"))
    )["total_qty"] or 0
    # print(automobile_qty)

    # -------------------------------
    # Merge Data
    # -------------------------------
    final_rows = []
    total_opening = total_procured = 0

    elv_types = VehicleType.objects.filter(userid=rvsf_id)

    for elv in elv_types:
        elv_name = elv.vehicle_type

        opening_qty = opening_dict.get(elv_name, 0)
        procured_qty = procured_dict.get(elv_name, 0)

        total_opening += opening_qty
        total_procured += procured_qty

        final_rows.append({
            "elv_name": elv_name,
            "opening_qty": opening_qty,
            "procured_qty": procured_qty,
            "available_qty": opening_qty + procured_qty,
        })

    context = {
        "rows": final_rows,
        "fy_list": fy_list,
        "selected_fy": selected_fy,
        "total_opening": total_opening,
        "total_procured": total_procured,
        "total_available": total_opening + total_procured,
        "automobile_qty" : automobile_qty,
    }

    return render(
        request,
        "procurement_detail/procurement_dashboard.html",
        context
    )

@csrf_exempt
def add_procurement_details(request):
    # rvsf_id = 49  # TODO: session based
    rvsf_id = request.session.get('user_id')
    # user_role = request.session.get('user_role')
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not rvsf_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not rvsf_id:
        return redirect("logoutrvsf")

    rvsf = RvsfRegistration.objects.get(id=rvsf_id)

    # FY logic
    incorp_fy = get_fy_from_date("01-05-2022")
    current_fy = get_current_financial_year()
    BASE_FY = "2025-2026"
    start_fy = incorp_fy if int(incorp_fy.split("-")[0]) > int(BASE_FY.split("-")[0]) else BASE_FY
    fy_list = generate_fy_range(start_fy, current_fy)

    elv_types = VehicleType.objects.filter(userid=rvsf_id)
    procurement_entries = ProcurementData.objects.filter(rvsf=rvsf).order_by("-created_at")
    producers=Registration.objects.all()
    
    # breakpoint()
    # ---------- COMMON CONTEXT ----------
    context = {
        "elv_types": elv_types,
        "fy_list": fy_list,
        "selected_fy": current_fy,
        "producers": producers,
        "procurement_entries": procurement_entries,
        "old": {},
    }

    if request.method == "POST":
        if not check_upload_limit(ProcurementData, rvsf_id, limit=5, minutes=10):
            messages.error(
                request,
                "Upload limit exceeded. You can upload only 5 files within 10 minutes."
            )
            return render(request, "procurement_detail/add_procurement_details.html", context)
        context["old"] = request.POST  # 🔑 keep old data
        vehicle_old_data = [
            {
                "vehicle_type": vt,
                "fuel_type": ft,
                "elv_count": ec,
                "invoice_number": inv
            }
            for vt, ft, ec, inv in zip(
                request.POST.getlist("vehicleType[]"),
                request.POST.getlist("fuelType[]"),
                request.POST.getlist("elvCount[]"),
                request.POST.getlist("invoiceNumber[]"),
            )
            if vt or ft or ec or inv
        ]
        context['vehicle_old_data'] = json.dumps(vehicle_old_data)
        
        allowed_vehicle_types = [v.vehicle_type for v in elv_types]
        allowed_fuel_types = ["Petrol", "Diesel", "EV", "Hybrid"]
        try:
            # -------------------------
            # COMMON REQUIRED FIELDS
            # -------------------------
            fy = request.POST.get("financial_year")
            procurement_date = request.POST.get("procurement_date")
            procurement_type = request.POST.get("procurement_type")

            if not fy or not procurement_date or not procurement_type:
                messages.error(request, "Financial Year, Procurement Date and Procurement Type are required.")
                return render(request, "procurement_detail/add_procurement_details.html", context)

            # -------------------------
            # ELV PROCUREMENT
            # -------------------------
            if procurement_type == "ELV":
                collection_type = request.POST.get("collection_type")

                if not collection_type:
                    messages.error(request, "Collection Centre Type is required.")
                    return render(request, "procurement_detail/add_procurement_details.html", context)

                source_name = request.POST.get("source_name")
                gst_number = request.POST.get("source_gst")
                address = request.POST.get("source_address")
                email = request.POST.get("source_email")
                
                # Allow only letters, numbers and spaces in name
                if source_name and not re.match(r'^[A-Za-z0-9 ]+$', source_name):
                    messages.error(request, "Special characters are not allowed in Name.")
                    return render(request, "procurement_detail/add_procurement_details.html", context)

                # Address allows letters, numbers, space, dot and slash
                if address and not re.match(r'^[A-Za-z0-9 ./]+$', address):
                    messages.error(request, "Only letters, numbers, space, dot (.) and slash (/) allowed in Address.")
                    return render(request, "procurement_detail/add_procurement_details.html", context)

                # Email validation (basic safe format)
                if email and not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', email):
                    messages.error(request, "Invalid email format.")
                    return render(request, "procurement_detail/add_procurement_details.html", context)
                
                if not is_valid_gst(gst_number):
                    messages.error(request, "Invalid GST Number format")
                    return render(request, "procurement_detail/add_procurement_details.html", context)

                if collection_type in ["collection-centres", "insurance-companies"]:
                    if not all([source_name, gst_number, address, email]):
                        messages.error(request, "All source details are required.")
                        return render(request, "procurement_detail/add_procurement_details.html", context)

                elif collection_type == "owner-elvs":
                    if not all([source_name, address, email]):
                        messages.error(request, "Owner name, address and email are required.")
                        return render(request, "procurement_detail/add_procurement_details.html", context)

                elif collection_type in ["bulk-consumer", "producers"]:
                    if not source_name:
                        messages.error(request, "Supplier / Entity name is required.")
                        return render(request, "procurement_detail/add_procurement_details.html", context)

                # -------------------------
                # VEHICLE ROW DATA
                # -------------------------
                vehicle_types = request.POST.getlist("vehicleType[]")
                fuel_types = request.POST.getlist("fuelType[]")
                elv_counts = request.POST.getlist("elvCount[]")
                invoice_numbers = request.POST.getlist("invoiceNumber[]")

                total_rows = len(vehicle_types)
                has_error = False

                # -------------------------
                # VALIDATION
                # -------------------------
                for i in range(total_rows):
                    # VALIDATE DROPDOWN VALUES
                    # -------------------------
                    if vehicle_types[i] not in allowed_vehicle_types:
                        messages.error(request, f"Invalid Vehicle Type selected (Row {i+1}).")
                        return render(request, "procurement_detail/add_procurement_details.html", context)

                    if fuel_types[i] not in allowed_fuel_types:
                        messages.error(request, f"Invalid Fuel Type selected (Row {i+1}).")
                        return render(request, "procurement_detail/add_procurement_details.html", context)
                    
                    cert_file = request.FILES.get(f"certificateUpload[{i}]")
                    invoice_file = request.FILES.get(f"invoiceFile[{i}]")
                    if not cert_file or not invoice_file:
                        messages.error(request, f"Certificate and Invoice file required (Row {i+1}).")
                        return render(request, "procurement_detail/add_procurement_details.html", context)
                    if not (
                            cert_file.name.lower().endswith(".pdf") and
                            invoice_file.name.lower().endswith(".pdf") and
                            cert_file.content_type == "application/pdf" and
                            invoice_file.content_type == "application/pdf"
                        ):
                        messages.error(request, f"Both Certificate and Invoice must be valid PDF files (Row {i+1}).")
                        return render(request, "procurement_detail/add_procurement_details.html", context)

                    # Optional: Check file size (5MB each)
                    if cert_file.size > 2 * 1024 * 1024 or invoice_file.size > 2 * 1024 * 1024:
                        messages.error(request, f"Each file must be under 2MB (Row {i+1}).")
                        return render(request, "procurement_detail/add_procurement_details.html", context)
                    
                    if not is_valid_pdf(cert_file):
                        messages.error(request, f"Invalid Certificate PDF format (Row {i+1}).")
                        return render(request, "procurement_detail/add_procurement_details.html", context)

                    if not is_valid_pdf(invoice_file):
                        messages.error(request, f"Invalid Invoice PDF format (Row {i+1}).")
                        return render(request, "procurement_detail/add_procurement_details.html", context)
                    
                    row_filled = any([
                        vehicle_types[i],
                        fuel_types[i],
                        elv_counts[i],
                        invoice_numbers[i],
                        cert_file,
                        invoice_file,
                    ])

                    if i == 0 or row_filled:
                        if not vehicle_types[i]:
                            messages.error(request, f"Vehicle Type required in row {i+1}")
                            has_error = True
                        if not fuel_types[i]:
                            messages.error(request, f"Fuel Type required in row {i+1}")
                            has_error = True
                        if not elv_counts[i]:
                            messages.error(request, f"ELV Quantity required in row {i+1}")
                            has_error = True
                        if elv_counts[i] and not elv_counts[i].isdigit():
                            messages.error(request, f"ELV Quantity must be numeric (Row {i+1}).")
                            return render(request, "procurement_detail/add_procurement_details.html", context)
                        if not cert_file:
                            messages.error(request, f"Certificate file required in row {i+1}")
                            has_error = True
                        if not invoice_numbers[i]:
                            messages.error(request, f"Invoice Number required in row {i+1}")
                            has_error = True
                        if invoice_numbers[i] and not re.match(r'^[A-Za-z0-9-]+$', invoice_numbers[i]):
                            messages.error(request, f"Invalid characters in Invoice Number (Row {i+1}).")
                            return render(request, "procurement_detail/add_procurement_details.html", context)
                        if not invoice_file:
                            messages.error(request, f"Invoice file required in row {i+1}")
                            has_error = True

                if has_error:
                    return render(request, "procurement_detail/add_procurement_details.html", context)

                # -------------------------
                # SAVE VEHICLE ROWS
                # -------------------------
                for i in range(total_rows):
                    cert_file = request.FILES.get(f"certificateUpload[{i}]")
                    invoice_file = request.FILES.get(f"invoiceFile[{i}]")

                    row_filled = any([
                        vehicle_types[i],
                        fuel_types[i],
                        elv_counts[i],
                        invoice_numbers[i],
                        cert_file,
                        invoice_file,
                    ])

                    if i == 0 or row_filled:
                        ProcurementData.objects.create(
                            rvsf=rvsf,
                            financial_year=fy,
                            procurement_date=procurement_date,
                            procurement_type="ELV",
                            collection_type=collection_type,
                            source_name=source_name,
                            gst_number=gst_number,
                            address=address,
                            email=email,
                            vehicle_type=vehicle_types[i],
                            fuel_type=fuel_types[i],
                            number_of_elvs=elv_counts[i],
                            certificate_of_deposit=cert_file,
                            invoice_number=invoice_numbers[i],
                            invoice_file=invoice_file,
                        )

            # -------------------------
            # SCRAP PROCUREMENT
            # -------------------------
            elif procurement_type == "AUTOMOBILE":
                scrap_entity = request.POST.get("scrap_entity_name")
                scrap_gst = request.POST.get("scrap_gst")
                scrap_address = request.POST.get("scrap_address")
                scrap_email = request.POST.get("scrap_email")
                scrap_qty = request.POST.get("scrapQuantity")
                scrap_invoice = request.POST.get("scrapInvoiceNumber")
                scrap_invoice_file = request.FILES.get("scrapInvoiceFile")
                if scrap_invoice and not re.match(r'^[A-Za-z0-9-]+$', scrap_invoice):
                    messages.error(request, "Invalid characters in Scrap Invoice Number.")
                    return render(request, "procurement_detail/add_procurement_details.html", context)
                # Name validation
                if scrap_entity and not re.match(r'^[A-Za-z0-9 ]+$', scrap_entity):
                    messages.error(request, "Special characters are not allowed in Entity Name.")
                    return render(request, "procurement_detail/add_procurement_details.html", context)

                # Address validation
                if scrap_address and not re.match(r'^[A-Za-z0-9 ./]+$', scrap_address):
                    messages.error(request, "Only letters, numbers, space, dot (.) and slash (/) allowed in Address.")
                    return render(request, "procurement_detail/add_procurement_details.html", context)

                # Email validation
                if scrap_email and not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', scrap_email):
                    messages.error(request, "Invalid email format.")
                    return render(request, "procurement_detail/add_procurement_details.html", context)
                if not all([scrap_entity, scrap_gst, scrap_address, scrap_qty, scrap_invoice, scrap_invoice_file]):
                    messages.error(request, "All Scrap fields are mandatory.")
                    return render(request, "procurement_detail/add_procurement_details.html", context)
                if not scrap_qty.isdigit():
                    messages.error(request, "Scrap Quantity must be numeric.")
                    return render(request, "procurement_detail/add_procurement_details.html", context)
                if not is_valid_gst(scrap_gst):
                    messages.error(request, "Invalid GST Number format")
                    return render(request, "procurement_detail/add_procurement_details.html", context)
                if not is_valid_pdf(scrap_invoice_file):
                    messages.error(request, "Invalid Scrap Invoice PDF.")
                    return render(request, "procurement_detail/add_procurement_details.html", context)
                ProcurementData.objects.create(
                    rvsf=rvsf,
                    financial_year=fy,
                    procurement_date=procurement_date,
                    procurement_type="AUTOMOBILE",
                    source_name=scrap_entity,
                    gst_number=scrap_gst,
                    address=scrap_address,
                    email=scrap_email,
                    number_of_elvs=scrap_qty,
                    invoice_number=scrap_invoice,
                    invoice_file=scrap_invoice_file,
                )

            messages.success(request, "Procurement details saved successfully.")
            return redirect("add_procurement_details")

        except Exception as e:
            messages.error(request, f"Unexpected error: {str(e)}")
            return render(request, "procurement_detail/add_procurement_details.html", context)

    return render(request, "procurement_detail/add_procurement_details.html", context)


def production_dashboard(request):
    # ------------------------------------
    # SESSION CHECK
    # ------------------------------------
    rvsf_id = request.session.get('user_id')
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not rvsf_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not rvsf_id:
        return redirect("logoutrvsf")

    rvsf = RvsfRegistration.objects.get(id=rvsf_id)

    # ------------------------------------
    # CATEGORIES
    # ------------------------------------
    # elv_category = Category.objects.get(name__iexact="Type of ELV")
    elv_category = Category.objects.get(name__iexact="End Of Life Vehicle (ELV)")
    automobile = Category.objects.get(name__iexact="Automobile Steel Scrap")

    # ------------------------------------
    # CURRENT FINANCIAL YEAR
    # ------------------------------------
    current_fy = get_current_financial_year()

    # =====================================================
    # 1. OPENING BALANCE (FY + RVSF WISE)
    # =====================================================
    opening_dict = {
        row["elv_type"]: row["opening_qty"] or 0
        for row in (
            OpeningBalance.objects
            .filter(
                financial_year__financial_year=current_fy,
                financial_year__rvsf_id=rvsf_id
            )
            .values("elv_type")
            .annotate(opening_qty=Sum("opening_balance_quantity"))
        )
    }

    # =====================================================
    # 2. PROCURED ELVs (FY WISE)
    # =====================================================
    procured_dict = {
        row["vehicle_type"]: row["procured_qty"] or 0
        for row in (
            ProcurementData.objects
            .filter(
                rvsf_id=rvsf_id,
                financial_year=current_fy,
                procurement_type="ELV"
            )
            .values("vehicle_type")
            .annotate(procured_qty=Sum("number_of_elvs"))
        )
    }

    # =====================================================
    # 3. PRODUCTION DATA (ELV WISE)
    # =====================================================
    production_data = (
        ProductionForm.objects
        .filter(category=elv_category)
        .values("elv_type")
        .annotate(
            total_scrapped_qty=Sum("scrapped_qty"),
            total_scrapped_weight=Sum("scrapped_weight"),
            total_steel_recovered=Sum("steel_scrap_recovered"),
            total_other_recovered=Sum("other_scrap_recovered"),
            total_cert_potential=Sum("cert_generating_potential"),
        )
    )

    production_map = {
        row["elv_type"]: row
        for row in production_data
    }

    # =====================================================
    # 4. FINAL ELV TABLE (REGISTERED VEHICLE TYPES)
    # =====================================================
    elv_data = []

    elv_types = VehicleType.objects.filter(userid=rvsf_id)

    for elv in elv_types:
        elv_type = elv.vehicle_type
        prod = production_map.get(elv_type, {})

        opening_qty = opening_dict.get(elv_type, 0)
        procured_qty = procured_dict.get(elv_type, 0)
        total_available = opening_qty + procured_qty

        scrapped_qty = prod.get("total_scrapped_qty", 0) or 0

        elv_data.append({
            "elv_type": elv_type,
            "opening_qty": opening_qty,
            "procured_qty": total_available,
            "total_available_qty": total_available,
            "total_scrapped_qty": scrapped_qty,
            "remaining_qty": total_available - scrapped_qty,
            "total_scrapped_weight": prod.get("total_scrapped_weight", 0) or 0,
            "total_steel_recovered": prod.get("total_steel_recovered", 0) or 0,
            "total_other_recovered": prod.get("total_other_recovered", 0) or 0,
            "total_cert_potential": prod.get("total_cert_potential", 0) or 0,
        })

    # =====================================================
    # 5. ELV TOTALS
    # =====================================================
    elv_totals = {
        "opening_qty": sum(r["opening_qty"] for r in elv_data),
        "procured_qty": sum(r["procured_qty"] for r in elv_data),
        "total_available_qty": sum(r["total_available_qty"] for r in elv_data),
        "total_scrapped_qty": sum(r["total_scrapped_qty"] for r in elv_data),
        "total_remaining_qty": sum(r["remaining_qty"] for r in elv_data),
        "total_scrapped_weight": sum(r["total_scrapped_weight"] for r in elv_data),
        "total_steel_recovered": sum(r["total_steel_recovered"] for r in elv_data),
        "total_other_recovered": sum(r["total_other_recovered"] for r in elv_data),
        "total_cert_potential": sum(r["total_cert_potential"] for r in elv_data),
    }

    # =====================================================
    # 6. AUTOMOBILE STEEL SCRAP
    # =====================================================
    auto_agg = (
        ProductionForm.objects
        .filter(category=automobile)
        .aggregate(
            total_processed=Sum("automobile_scrap_processed"),
            total_steel_recovered=Sum("steel_scrap_recovered"),
            total_cert_potential=Sum("cert_generating_potential"),
        )
    )

    # auto_procured = 9564  # keep static if required
    auto_procured = (
            ProcurementData.objects
            .filter(
                rvsf_id=rvsf_id,
                financial_year=current_fy,
                procurement_type="AUTOMOBILE"
            )
            .aggregate(total_qty=Sum("number_of_elvs"))
        )["total_qty"] or 0
    auto_processed = auto_agg["total_processed"] or 0
    auto_recovered = auto_agg["total_steel_recovered"] or 0

    auto_data = [{
        "scrap_name": "Automobile Steel Scrap",
        "processed_qty": auto_processed,
        "procured_qty": auto_procured,
        "total_steel_recovered": auto_recovered,
        "remaining_qty": auto_procured - auto_processed,
        "total_cert_potential": auto_agg["total_cert_potential"] or 0,
    }]

    auto_totals = {
        "procured_qty": auto_procured,
        "processed_qty": auto_processed,
        "total_steel_recovered": auto_recovered,
        "total_remaining_qty": auto_procured - auto_recovered,
        "total_cert_potential": auto_agg["total_cert_potential"] or 0,
    }

    # =====================================================
    # 7. OTHER SCRAP
    # =====================================================
    wasteType = (
        OtherScrap.objects
        .values("wasteType")
        .annotate(total_qty=Sum("quantity"))
    )

    other_scrap = [{
        "wasteType": row["wasteType"],
        "total_qty": row["total_qty"] or 0
    } for row in wasteType]

    other_scrap_totals = {
        "total_qty": sum(r["total_qty"] for r in other_scrap),
    }

    # =====================================================
    # RENDER
    # =====================================================
    context = {
        "elv_data": elv_data,
        "elv_totals": elv_totals,
        "auto_data": auto_data,
        "auto_totals": auto_totals,
        "other_scrap": other_scrap,
        "other_scrap_totals": other_scrap_totals,
    }

    return render(
        request,
        "production_details/production_dashboard.html",
        context
    )



def production_form(request):
    user_id = request.session.get('user_id')
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not user_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not user_id:
        return redirect("logoutrvsf")

    # ------------------------------------
    # Master data
    # ------------------------------------
    elv_types = VehicleType.objects.filter(userid=user_id)
    plantCapacity = PlantCapacity.objects.filter(userid=user_id).first()
    # categories = Category.objects.all().order_by('-id')
    categories = Category.objects.order_by('id').values('id', 'name')

    # ------------------------------------
    # Financial Year
    # ------------------------------------
    current_fy = get_current_financial_year()

    # ------------------------------------
    # Opening Balance (FY + RVSF)
    # ------------------------------------
    opening_dict = {
        row["elv_type"]: row["qty"] or 0
        for row in (
            OpeningBalance.objects
            .filter(
                financial_year__financial_year=current_fy,
                financial_year__rvsf_id=user_id
            )
            .values("elv_type")
            .annotate(qty=Sum("opening_balance_quantity"))
        )
    }

    # ------------------------------------
    # Procured ELVs (FY)
    # ------------------------------------
    procured_dict = {
        row["vehicle_type"]: row["qty"] or 0
        for row in (
            ProcurementData.objects
            .filter(
                rvsf_id=user_id,
                financial_year=current_fy,
                procurement_type="ELV"
            )
            .values("vehicle_type")
            .annotate(qty=Sum("number_of_elvs"))
        )
    }

    # ------------------------------------
    # Total Available ELVs (ALL TYPES)
    # ------------------------------------
    total_available_elvs = sum(
        opening_dict.get(v.vehicle_type, 0) +
        procured_dict.get(v.vehicle_type, 0)
        for v in elv_types
    )

    # ------------------------------------
    # History
    # ------------------------------------
    history = (
        ProductionForm.objects
        .select_related("category")
        .filter(rvsf_id=user_id)
        .order_by("-created_at")
    )
    print(categories.values(), "11111111111111111111111")
    context = {
        "category": categories,
        "elvType": elv_types,                  # 🔥 FIXED name
        "plantCapacity": plantCapacity,
        "procuredElvs": total_available_elvs,  # 🔥 REAL value
        "history": history,
    }

    return render(
        request,
        "production_details/scrap_generation_form.html",
        context
    )



# @csrf_exempt
def save_production_form(request):

    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Invalid request"},
            status=400
        )

    user_id = request.session.get("user_id")
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not user_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not user_id:
        return redirect("logoutrvsf")
    # RATE LIMIT CHECK (5 per 10 min)
    # ===============================
    if not check_upload_limit(ProductionForm, user_id, limit=5, minutes=10):
        return JsonResponse({
            "status": "error",
            "message": "Upload limit exceeded. You can submit only 5 production entries within 10 minutes."
        }, status=429)
        
    elv_types = VehicleType.objects.filter(userid=user_id)
    allowed_elv_types = {v.vehicle_type for v in elv_types}
    try:
        data = json.loads(request.body)
        # breakpoint()
        category_id = data.get("category")

        # Check category is provided
        if not category_id:
            return JsonResponse({
                "status": "error",
                "message": "Category is required."
            }, status=400)

        # Check category exists
        category = Category.objects.filter(id=category_id).first()

        if not category:
            return JsonResponse({
                "status": "error",
                "message": "Invalid category selected."
            }, status=400)
        # STRICT NUMERIC VALIDATION
        # (Only Positive Integer or Decimal)
        # ===============================
        decimal_pattern = re.compile(r'^\d+(\.\d+)?$')

        numeric_fields = [
            "automobile_scrap_processed",
            "steel_scrap_recovered",
            "scrapped_weight",
            "scrapped_qty",
            "other_scrap_recovered",
            "cert_generating_potential",
        ]

        for field in numeric_fields:
            value = data.get(field)

            if value not in (None, "", 0):
                value_str = str(value).strip()

                # 1️⃣ Format validation
                if not decimal_pattern.match(value_str):
                    return JsonResponse({
                        "status": "error",
                        "message": f"Invalid numeric value for {field}. Only positive numbers are allowed."
                    }, status=400)

                # 2️⃣ Extra negative safety check (double protection)
                if Decimal(value_str) < 0:
                    return JsonResponse({
                        "status": "error",
                        "message": f"{field} cannot be negative."
                    }, status=400)


        # Validate nested other_scraps quantities
        name_pattern = re.compile(r'^[A-Za-z0-9 ]+$')
        for scrap in data.get("other_scraps", []):
            qty = scrap.get("quantity")
             # Validate waste type (letters, numbers, spaces only)
            if waste_type and not name_pattern.match(waste_type):
                return JsonResponse({
                    "status": "error",
                    "message": "Waste Type can contain only letters, numbers and spaces."
                }, status=400)
            if qty not in (None, "", 0):
                qty_str = str(qty).strip()

                if not decimal_pattern.match(qty_str):
                    return JsonResponse({
                        "status": "error",
                        "message": "Invalid numeric value in other scraps quantity."
                    }, status=400)

                if Decimal(qty_str) < 0:
                    return JsonResponse({
                        "status": "error",
                        "message": "Other scrap quantity cannot be negative."
                    }, status=400)
        # fy = request.POST.get("financial_year") Need to uncomment when front end send the financial year
        fy = get_current_financial_year()
        # Convert to Decimal safely
        # if data.get("automobile_scrap_processed"):
        #     scrapped_weight = Decimal(str(data.get("automobile_scrap_processed", 0)))
        other_scrap_recovered = None
        steel_scrap_recovered = Decimal("0")    

        if data.get("automobile_scrap_processed"):

            scrapped_weight = Decimal(str(data.get("automobile_scrap_processed", 0)))
            steel_scrap_recovered = Decimal(str(data.get("steel_scrap_recovered", 0)))

            auto_agg = (
                ProductionForm.objects
                .filter(category_id= 2)
                .aggregate(
                    total_processed=Sum("automobile_scrap_processed"),
                )
            )

            auto_procured = (
                    ProcurementData.objects
                    .filter(
                        rvsf_id=user_id,
                        procurement_type="AUTOMOBILE"
                    )
                    .aggregate(total_qty=Sum("number_of_elvs"))
                )["total_qty"] or Decimal("0")
            already_processed = auto_agg["total_processed"] or Decimal("0")

            remaining_weight = [{
                "remaining_qty": auto_procured - already_processed,
                }]

            # remaining_weight = max_elv_weight - already_processed

            if scrapped_weight < steel_scrap_recovered:
                return JsonResponse({
                    "status": "error",
                    "message": "Automobile scrap processed cannot be greater than Steel Scrap Recovered"
                }, status=400)
                
            if scrapped_weight > remaining_weight[0]["remaining_qty"]:
                return JsonResponse({
                    "status": "error",
                    "message": "Automobile scrap processed cannot exceed remaining Automobile steel scrap weight"
                }, status=400)

        # else:
        #     scrapped_weight = Decimal(str(data.get("scrapped_weight", 0)))


        else:
            scrapped_weight = Decimal(str(data.get("scrapped_weight", 0)))
            scrapped_qty = Decimal(str(data.get("scrapped_qty", 0)))
            elv_type = data.get("elv_type")
            
            if elv_type not in allowed_elv_types:
                return JsonResponse({
                    "status": "error",
                    "message": "Invalid ELV type selected."
                }, status=400)

            # 1️⃣ Already scrapped ELVs
            elv_agg = (
                ProductionForm.objects
                .filter(
                    rvsf_id=user_id,
                    elv_type=elv_type
                )
                .aggregate(total_scrapped=Sum("scrapped_qty"))
            )
            already_scrapped_qty = elv_agg["total_scrapped"] or Decimal("0")

            # 2️⃣ Procured ELVs
            elv_procured = (
                ProcurementData.objects
                .filter(
                    rvsf_id=user_id,
                    procurement_type="ELV",
                    vehicle_type=elv_type
                )
                .aggregate(total_qty=Sum("number_of_elvs"))
            )["total_qty"] or Decimal("0")

            financial_year_obj = FinancialYear.objects.filter(
                rvsf_id=user_id,
            ).first()

            opening_balance_qty = Decimal("0")

            if financial_year_obj:
                opening_balance_qty = (
                    OpeningBalance.objects
                    .filter(
                        financial_year=financial_year_obj,
                        elv_type=elv_type
                    )
                    .aggregate(total=Sum("opening_balance_quantity"))
                )["total"] or Decimal("0")
            remaining_qty = elv_procured + opening_balance_qty - already_scrapped_qty
            
            # 3️⃣ Validation
            if scrapped_qty > remaining_qty:
                return JsonResponse({
                    "status": "error",
                    "message": (
                        f"Scrapped quantity ({scrapped_qty}) exceeds "
                        f"remaining ELV quantity ({remaining_qty}) for ELV type {elv_type}"
                    )
                }, status=400)

            steel_scrap_recovered = Decimal(str(data.get("steel_scrap_recovered", 0)))
            # other_scrap_recovered = Decimal(str(data.get("other_scrap_recovered", 0)))
            other_scrap_recovered = Decimal(str(data.get("other_scrap_recovered", 0)))

            # ===============================
            # VALIDATIONS
            # ===============================

            max_steel = scrapped_weight * Decimal("0.65")
            # max_other = scrapped_weight * Decimal("0.35")
            
            base_weight = scrapped_weight - steel_scrap_recovered
            max_other = base_weight
            min_other = base_weight * Decimal("0.80")

            if steel_scrap_recovered > max_steel:
                return JsonResponse({
                    "status": "error",
                    "message": "Steel scrap recovered cannot exceed 65% of scrapped weight"
                }, status=400)

            if not (min_other <= other_scrap_recovered <= max_other):
                return JsonResponse({
                    "status": "error",
                    "message": "Entered quantity of other waste is not in range limit."
                }, status=400)
                
            if other_scrap_recovered > steel_scrap_recovered:
                return JsonResponse({
                    "status": "error",
                    "message": "Other scrap recovered cannot be greater than Steel Scrap Recovered"
                }, status=400)


        
        category = Category.objects.get(id=data["category"])
        scrapping_date = parse_date(data["scrapping_date"])

        # ===============================
        # SAVE DATA (TRANSACTION SAFE)
        # ===============================
        with transaction.atomic():

            entry = ProductionForm.objects.create(
                rvsf_id=user_id,
                category=category,
                scrapping_date=scrapping_date,
                financial_year=fy,
                elv_type=data.get("elv_type"),
                scrapped_qty=data.get("scrapped_qty") or 0,
                scrapped_weight=scrapped_weight,

                automobile_scrap_processed=data.get("automobile_scrap_processed") or 0,

                steel_scrap_recovered=steel_scrap_recovered,
                other_scrap_recovered=other_scrap_recovered,
                cert_generating_potential=data.get("cert_generating_potential") or 0,
            )

            for scrap in data.get("other_scraps", []):
                qty = Decimal(str(scrap.get("quantity", 0)))
                if qty > 0:
                    OtherScrap.objects.create(
                        rvsf_id=user_id,
                        production=entry,
                        financial_year=fy,
                        wasteType=scrap.get("wasteType"),
                        quantity=qty
                    )

        return JsonResponse({
            "status": "success",
            "message": "Production entry saved successfully",
            "id": entry.id
        })

    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": str(e)},
            status=500
        )



def waste_dashboard(request):

    rvsf_id = request.session.get("user_id")
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not rvsf_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not rvsf_id:
        return redirect("logoutrvsf")
    selected_fy = request.GET.get("fyyear")
    # -------------------------
    # Recovered quantities
    # -------------------------
    recovered_qs = OtherScrap.objects.filter(rvsf_id=rvsf_id)

    if selected_fy:
        recovered_qs = recovered_qs.filter(financial_year=selected_fy)

    recovered_qs = (
        recovered_qs
        .values("wasteType")
        .annotate(recovered_qty=Sum("quantity"))
    )

    recovered_map = {
        (row["wasteType"]): row["recovered_qty"]
        for row in recovered_qs
    }

    # -------------------------
    # Processed quantities
    # -------------------------
    processed_qs = (
        WasteProcessing.objects
        .filter(rvsf_id=rvsf_id)
        .values("waste_type", "activity")
        .annotate(total_qty=Sum("processed_qty"))
    )
    financial_years_list = (
        OtherScrap.objects
        .filter(rvsf_id=rvsf_id)
        .values_list("financial_year", flat=True)
        .distinct()
    )
    print(processed_qs, "11111111111111111111")
    # Build structure
    dashboard_data = {}

    for (waste), qty in recovered_map.items():
        dashboard_data[(waste)] = {
            "recovered_waste": waste,
            "recovered_qty": qty or Decimal("0"),
            "qty_recycled": Decimal("0"),
            "qty_refurbished": Decimal("0"),
            "qty_disposed": Decimal("0"),
             
        }

    for row in processed_qs:
        waste = row["waste_type"]
        activity = row["activity"]
        qty = row["total_qty"] or Decimal("0")

        if (waste) not in dashboard_data:
            continue

        if activity == "recycled":
            dashboard_data[(waste)]["qty_recycled"] = qty
        elif activity == "refurbish":
            dashboard_data[(waste)]["qty_refurbished"] = qty
        elif activity == "disposal":
            dashboard_data[(waste)]["qty_disposed"] = qty

    # -------------------------
    # Remaining quantity
    # -------------------------
    elv_data = []
    for data in dashboard_data.values():
        total_processed = (
            data["qty_recycled"]
            + data["qty_refurbished"]
            + data["qty_disposed"]
        )
        data["remaining_qty"] = data["recovered_qty"] - total_processed
        elv_data.append(data)
    print(elv_data, "22222222222222222222222")
    return render(
        request,
        "waste_detail/waste_dashboard.html",
        {
            "elv_data": elv_data,
         "financial_years_list": financial_years_list
         }
        
    )
        


def waste_form(request):

    rvsf_id = request.session.get("user_id")
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not rvsf_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not rvsf_id:
        return redirect("logoutrvsf")

    try:

        # =========================
        # OTHER SCRAP SUMMARY (Total Generated)
        # =========================
        waste_summary_qs = (
            OtherScrap.objects
            .filter(rvsf_id=rvsf_id)
            .values("wasteType")
            .annotate(total_quantity=Sum("quantity"))
        )

        # =========================
        # PROCESSED WASTE SUMMARY (For Remaining Calculation)
        # =========================
        processed_summary = (
            WasteProcessing.objects
            .filter(rvsf_id=rvsf_id)
            .values("waste_type")
            .annotate(total_quantity=Sum("processed_qty"))
        )
        print(processed_summary,rvsf_id,'fsdfsaad')

        # Convert processed summary into dictionary
        processed_map = {
            item["waste_type"]: item["total_quantity"] or Decimal("0")
            for item in processed_summary
        }

        # =========================
        # CALCULATE REMAINING QUANTITY
        # =========================
        adjusted_waste_list = []

        for item in waste_summary_qs:
            waste_type = item["wasteType"]
            total_qty = item["total_quantity"] or Decimal("0")

            processed_qty = processed_map.get(waste_type, Decimal("0"))
            remaining_qty = total_qty - processed_qty

            if remaining_qty > 0:
                adjusted_waste_list.append({
                    "wasteType": waste_type,
                    "remaining_quantity": remaining_qty
                })

        # =========================
        # FULL TABLE DATA (Using values())
        # =========================
        waste_list = (
            WasteProcessing.objects
            .filter(rvsf_id=rvsf_id)
            .values(
                "id",
                "waste_type",
                "activity",
                "processed_qty",
                "buyer_name",
                "gst_number",
                "sale_date",
                "invoice",
                "invoice_number"
            )
            .order_by("-id")
        )

        context = {
            "waste_summary": adjusted_waste_list,
            "waste_list": waste_list,
        }
        print(context, "111111111111111111111111111")
        return render(
            request,
            "waste_detail/add_waste_details.html",
            context
        )

    except Exception as e:
        messages.error(request, f"Unexpected error occurred: {e}")
        return render(
            request,
            "waste_detail/add_waste_details.html",
            {
                "waste_summary": [],
                "waste_list": [],
            }
        )


def save_waste_form(request):
    rvsf_id = request.session.get("user_id")
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not rvsf_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not rvsf_id:
        return redirect("logoutrvsf")

    if request.method == "POST":
        if not check_upload_limit(WasteProcessing, rvsf_id, limit=5, minutes=10):
            messages.error(
                request,
                "Upload limit exceeded. You can submit only 5 waste entries within 10 minutes."
            )
            return redirect("waste_form")

        waste_type = request.POST.get("waste_type")
        activity = request.POST.get("activity")
        qty = request.POST.get("qty")
        buyer_name = request.POST.get("buyer_name")
        gst = request.POST.get("gst")
        buyer_address = request.POST.get("address")
        email = request.POST.get("email")
        sale_date = request.POST.get("sale_date")
        invoice_number = request.POST.get("invoice_number")
        current_fy = get_current_financial_year()
        invoice = request.FILES.get("invoice")
        manifest_document = request.FILES.get("manifest_document")
        tsdf_document = request.FILES.get("tsdf_document")


        if not all([waste_type, activity, qty, buyer_name, gst, buyer_address, sale_date]):
            messages.error(request, "Please fill all required fields.")
            return redirect("waste_form")
        allowed_activities = {"recycled", "refurbish", "disposal"}

        if activity not in allowed_activities:
            messages.error(request, "Invalid activity selected.")
            return redirect("waste_form")
        # Validate waste type exists in OtherScrap
        if not OtherScrap.objects.filter(rvsf_id=rvsf_id, wasteType=waste_type).exists():
            messages.error(request, "Invalid Waste Type selected.")
            return redirect("waste_form")
        if buyer_name and not re.match(r'^[A-Za-z0-9 ]+$', buyer_name):
            messages.error(request, "Special characters are not allowed in Buyer Name.")
            return redirect("waste_form")

        # Address
        if buyer_address and not re.match(r'^[A-Za-z0-9 ./]+$', buyer_address):
            messages.error(request, "Only letters, numbers, space, dot (.) and slash (/) allowed in Address.")
            return redirect("waste_form")

        # Email
        if email and not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', email):
            messages.error(request, "Invalid email format.")
            return redirect("waste_form")

        # Invoice Number
        if invoice_number and not re.match(r'^[A-Za-z0-9-]+$', invoice_number):
            messages.error(request, "Invalid characters in Invoice Number.")
            return redirect("waste_form")

        # Quantity (positive decimal only)
        if not re.match(r'^\d+(\.\d+)?$', str(qty)):
            messages.error(request, "Quantity must be a positive number.")
            return redirect("waste_form")
        if not invoice:
            messages.error(request, "Invoice document is required.")
            return redirect("waste_form")

        if not is_valid_pdf(invoice):
            messages.error(request, "Invoice must be a valid PDF under 2MB.")
            return redirect("waste_form")
        

        if not is_valid_gst(gst):
                messages.error(request, "Invalid GST Number format")
                return redirect("waste_form")
                
        # Disposal-specific validation
        if activity.lower() == "disposal":
            if not manifest_document or not tsdf_document:
                messages.error(
                    request,
                    "Manifest and TSDF document are required for disposal activity."
                )
                return redirect("waste_form")

            # Validate both
            if not is_valid_pdf(manifest_document):
                messages.error(request, "Manifest document must be a valid PDF under 2MB.")
                return redirect("waste_form")

            if not is_valid_pdf(tsdf_document):
                messages.error(request, "TSDF document must be a valid PDF under 2MB.")
                return redirect("waste_form")

        try:
            qty = Decimal(qty)

            total_recovered = (
                OtherScrap.objects
                .filter(rvsf_id=rvsf_id, wasteType=waste_type)
                .aggregate(total=Sum("quantity"))
            )["total"] or Decimal("0")

            total_processed = (
                WasteProcessing.objects
                .filter(rvsf_id=rvsf_id, waste_type=waste_type)
                .aggregate(total=Sum("processed_qty"))
            )["total"] or Decimal("0")

            remaining_qty = total_recovered - total_processed

            if qty > remaining_qty:
                messages.error(
                    request,
                    f"Entered quantity ({qty}) exceeds available scrap ({remaining_qty})."
                )
                return redirect("waste_form")

            # ✅ Save
            WasteProcessing.objects.create(
                rvsf_id=rvsf_id,
                waste_type=waste_type,
                activity=activity,
                processed_qty=qty,
                buyer_name=buyer_name,
                buyer_address=buyer_address,
                buyer_email=email,
                gst_number=gst,
                sale_date=sale_date,
                invoice_number=invoice_number,
                invoice=invoice,
                manifest_document=manifest_document,
                agreement_tsdf_certificate=tsdf_document,
                financial_year = current_fy 
            )

            messages.success(request, "✅ Waste details submitted successfully.")
            return redirect("waste_form")

        except Exception as e:
            messages.error(request, f"❌ Error while saving data: {str(e)}")
            return redirect("waste_form")

    messages.error(request, "Invalid request.")
    return redirect("waste_form")



def certificate_generation_dashboard(request):
    
    user_id = request.session.get("user_id")
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not user_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not user_id:
        return redirect("logoutrvsf")

    try:
        ratio_data = calculate_steel_recovery_data(user_id)
    except ValueError as e:
        messages.error(request, str(e))
        return render(
        request, "epr_certificate_generation/epr_certificate_generation_dashboard.html")

    qtySteelRecovered = ratio_data["qtySteelRecovered"]

    # ---------------------------------------
    # 6️⃣ Certificate Potential
    # ---------------------------------------

    certGeneratedPotential = (
        ProductionForm.objects
        .filter(rvsf_id=user_id)
        .aggregate(total=Sum("cert_generating_potential"))
    )["total"] or Decimal("0")

    steelScrapSold = ratio_data["steel_scrap_sold"]

    # Prevent overselling
    steelScrapSold = min(steelScrapSold, qtySteelRecovered)

    remainSteelScrap = qtySteelRecovered - steelScrapSold

    eprCertGenerated = steelScrapSold

    remainCertPotential = max(
        certGeneratedPotential - eprCertGenerated,
        Decimal("0")
    )
    
    context = {
        "qtySteelRecovered": qtySteelRecovered,
        "certGeneratedPotential": certGeneratedPotential,
        "steelScrapSold": steelScrapSold,
        "remainSteelScrap": remainSteelScrap,
        "eprCertGenerated": eprCertGenerated,
        "remainCertPotential": remainCertPotential,
    }

    return render(
        request,
        "epr_certificate_generation/epr_certificate_generation_dashboard.html",
        context
    )




def certificate_generation_form(request):

    user_id = request.session.get("user_id")
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not user_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not user_id:
        return redirect("logoutrvsf")

    history = (
        SteelScrapSale.objects
        .filter(rvsf_id=user_id)
        .order_by("-created_at")
    )

    context = {
        "history": history
    }

    if request.method == "POST":
        if not check_upload_limit(SteelScrapSale, user_id, limit=5, minutes=10):
            messages.error(
                request,
                "Upload limit exceeded. You can submit only 5 steel sale entries within 10 minutes."
            )
            return redirect("certificate_generation_form")
        try:
            required_fields = [
                "date_of_sale", "buyer_type", "buyer_name",
                "buyer_address", "gst_number", "email",
                "quantity_sold", "invoice_amount", "invoice_number",
            ]
            for field in required_fields:
                if not request.POST.get(field):
                    messages.error(request, f"Please fill all {field} details.")
                    return redirect("certificate_generation_form")
            buyer_name = request.POST.get("buyer_name")
            buyer_address = request.POST.get("buyer_address")
            email = request.POST.get("email")
            invoice_number = request.POST.get("invoice_number")
            invoice_amount = request.POST.get("invoice_amount")
            quantity_sold = request.POST.get("quantity_sold")
            gst_number = request.POST.get("gst_number")
            buyer_type = request.POST.get("buyer_type")
            allowed_buyer_types = {
                "Blast Furnace",
                "Induction Furnace",
                "Electric Arc Furnace",
                "Scrap Recyclers",
                "Steel Mills",
                "Others"
            }

            if buyer_type not in allowed_buyer_types:
                messages.error(request, "Invalid Buyer Type selected.")
                return redirect("certificate_generation_form")

            # Buyer Name (letters, numbers, space only)
            if buyer_name and not re.match(r'^[A-Za-z0-9 ]+$', buyer_name):
                messages.error(request, "Special characters are not allowed in Buyer Name.")
                return redirect("certificate_generation_form")

            # Address (allow . and /)
            if buyer_address and not re.match(r'^[A-Za-z0-9 ./]+$', buyer_address):
                messages.error(request, "Only letters, numbers, space, dot (.) and slash (/) allowed in Address.")
                return redirect("certificate_generation_form")

            # Email validation
            if email and not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', email):
                messages.error(request, "Invalid email format.")
                return redirect("certificate_generation_form")

            # Invoice number (letters, numbers, dash only)
            if invoice_number and not re.match(r'^[A-Za-z0-9-]+$', invoice_number):
                messages.error(request, "Invalid characters in Invoice Number.")
                return redirect("certificate_generation_form")

            # GST validation
            if not is_valid_gst(gst_number):
                messages.error(request, "Invalid GST Number format.")
                return redirect("certificate_generation_form")

            # Quantity sold (positive decimal only)
            if not re.match(r'^\d+(\.\d+)?$', str(quantity_sold)):
                messages.error(request, "Quantity sold must be a positive number.")
                return redirect("certificate_generation_form")

            # Invoice amount (positive decimal only)
            if not re.match(r'^\d+(\.\d+)?$', str(invoice_amount)):
                messages.error(request, "Invoice amount must be a positive number.")
                return redirect("certificate_generation_form")
            # ------------------------
            # FILE VALIDATION
            # ------------------------

            invoice_file = request.FILES.get("invoice_file")

            # Required Check
            if not invoice_file:
                messages.error(request, "Invoice file is required.")
                return redirect("certificate_generation_form")

            # PDF Validation (Size + Structure + Extension)
            if not is_valid_pdf(invoice_file):
                messages.error(request, "Invoice must be a valid PDF file under 2MB.")
                return redirect("certificate_generation_form")

            # 🔥 NEW COMPLETE BUSINESS LOGIC (13:7 WITH VALIDATION)
            current_fy = get_current_financial_year()
            # 1️⃣ Total Other Scrap Recovered
            total_other_scrap_recovered = (
                OtherScrap.objects
                .filter(rvsf_id=user_id)
                .aggregate(total=Sum("quantity"))
            )["total"] or Decimal("0")

            # 2️⃣ Total Other Scrap Processed
            total_other_scrap_processed = (
                WasteProcessing.objects
                .filter(rvsf_id=user_id)
                .aggregate(total=Sum("processed_qty"))
            )["total"] or Decimal("0")

            # 3️⃣ HARD VALIDATION
            if total_other_scrap_processed > total_other_scrap_recovered:
                messages.error(
                    request,
                    "Processed waste exceeds total recovered scrap. Please correct waste entries."
                )
                return redirect("certificate_generation_form")

            
            try:
                ratio_data = calculate_steel_recovery_data(user_id)
            except ValueError as e:
                messages.error(request, str(e))
                return render(request, "epr_certificate_generation/epr_certificate_form.html",)

            qtySteelRecovered = ratio_data["qtySteelRecovered"]
            steelScrapSold = ratio_data["steel_scrap_sold"]

            remainSteelScrap = qtySteelRecovered - steelScrapSold

            # 9️⃣ Sale Validation
            quantity_sold = Decimal(request.POST.get("quantity_sold"))

            if quantity_sold > remainSteelScrap:
                messages.error(
                    request,
                    "Sale quantity can't exceeds Remaining steel Scrap Quantity at RVSF(MT)."
                )
                return redirect("certificate_generation_form")

            # ============================================================
            # SAVE DATA
            # ============================================================

            with transaction.atomic():

                
                if buyer_type == "Others":
                    buyer_type = f"Others - {request.POST.get('other_buyer_type')}"

                SteelScrapSale.objects.create(
                    rvsf_id=user_id,
                    sale_date=request.POST.get("date_of_sale"),
                    buyer_type=buyer_type,
                    buyer_name=request.POST.get("buyer_name"),
                    buyer_address=request.POST.get("buyer_address"),
                    gst_number=request.POST.get("gst_number"),
                    email=request.POST.get("email"),
                    quantity_sold=quantity_sold,
                    invoice_amount=request.POST.get("invoice_amount"),
                    invoice_number=request.POST.get("invoice_number"),
                    invoice_pdf=invoice_file,
                    financial_year = current_fy 
                )

            messages.success(request, "✅ Steel sale recorded successfully.")
            return redirect("certificate_generation_form")

        except Exception as e:
            messages.error(request, "Error 500.")
            return redirect("certificate_generation_form")

    else:
        return render(
            request,
            "epr_certificate_generation/epr_certificate_form.html",
            context
        )

def denominate_epr_dashboard(request):
    
    rvsf_id = request.session.get("user_id")
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not rvsf_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not rvsf_id:
        return redirect("logoutrvsf")

    # -------------------------
    # FETCH GENERATED CERTS
    # -------------------------
    cert_generated = (
        SteelScrapSale.objects
        .filter(rvsf_id=rvsf_id)
        .aggregate(total=Sum("quantity_sold"))
        .get("total") or Decimal("0")
    )
    today = now()

    certDenominated = (DenominatedCertificate.objects
        .filter(rvsf_id=rvsf_id,
                expiry_date__gte=today)
        .aggregate(total=Sum("total_certificate_value_denominated"))
        .get("total") or Decimal("0")
    )
    remainCertAvailDenominated = cert_generated - certDenominated
    denomination_details = (
        DenominationDetail.objects
        .filter(
            rvsf_id=rvsf_id,
            denomination_master__expiry_date__gte=today
        )
        .select_related("denomination_master")
        .values(
            "unique_id",
            "denomination_kg",
            "quantity",
            "denomination_master__denomination_date",
            "denomination_master__expiry_date",
        )
        .order_by("-denomination_master__denomination_date")
    )
    context = {
        "certGenerated" : cert_generated,
        "certDenominated" : certDenominated,
        "remainCertAvailDenominated" : remainCertAvailDenominated,
        "denomination_details": denomination_details,
    }
    
    return render(request, "denominate_epr_certificate/denominate_dashboard.html", context) 


def denominate_epr_certificate(request):
    rvsf_id = request.session.get("user_id")
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not rvsf_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not rvsf_id:
        return redirect("logoutrvsf")
    today = now()
    if request.method == 'POST':
        
        try:
            decimal_pattern = re.compile(r'^\d+(\.\d+)?$')
            integer_pattern = re.compile(r'^\d+$')

            total_mt_raw = request.POST.get("total_certificate_value_denominated", "").strip()

            if not decimal_pattern.match(total_mt_raw):
                messages.error(request, "Total certificate value must be a positive number.")
                return redirect("denominate_dashboard")

            if Decimal(total_mt_raw) <= 0:
                messages.error(request, "Total certificate value must be greater than zero.")
                return redirect("denominate_dashboard")

            # Validate denomination quantities (must be positive integers only)
            denomination_fields = ["kg_100", "kg_200", "kg_500", "kg_1000", "kg_10000"]

            if not any(request.POST.get(field) for field in denomination_fields):
                messages.error(request, "Please enter at least one denomination quantity.")
                return redirect("denominate_dashboard")
            for field in denomination_fields:
                value = request.POST.get(field, "").strip()

                if value:
                    if not integer_pattern.match(value):
                        messages.error(request, f"Invalid quantity for {field}. Only positive integers allowed.")
                        return redirect("denominate_dashboard")

                    if int(value) < 0:
                        messages.error(request, f"{field} quantity cannot be negative.")
                        return redirect("denominate_dashboard")
            total_mt = Decimal(request.POST.get("total_certificate_value_denominated", "0"))
            state_code = RvsfRegistration.objects.get(id=rvsf_id).state
            print("111111111111111111")
            denomination_map = {
                100: request.POST.get("kg_100"),
                200: request.POST.get("kg_200"),
                500: request.POST.get("kg_500"),
                1000: request.POST.get("kg_1000"),
                10000: request.POST.get("kg_10000"),
            }

            # ------------------------
            # VALIDATION
            # ------------------------
            total_kg = Decimal("0")

            for kg, qty in denomination_map.items():
                # qty = Decimal(qty or 0)
                qty = Decimal(str(qty or 0))
                total_kg += kg * qty

            if (total_kg / Decimal("1000")) != total_mt:
                messages.error(
                    request,
                    "Denomination total must exactly match certificate value."
                )
                return redirect("denominate_dashboard")
            current_year = get_current_financial_year()
            # ------------------------
            # SAVE (DB SEQUENCE SAFE)
            # ------------------------
            with transaction.atomic():

                master = DenominatedCertificate.objects.create(
                    rvsf_id=rvsf_id,
                    total_certificate_value_denominated=total_mt,
                    denomination_date=now(),
                    financial_year = current_year
                )

                for kg, qty in denomination_map.items():
                    qty = int(qty or 0)
                    if qty <= 0:
                        continue

                    # Save first to get DB sequence (id)
                    detail = DenominationDetail.objects.create(
                        denomination_master=master,
                        rvsf_id=rvsf_id,
                        denomination_kg=kg,
                        quantity=qty,
                        unique_id="TEMP"
                    )

                    # Generate unique ID using DB PK
                    unique_id = (
                        f"{rvsf_id}_"
                        f"{now().strftime('%Y%m%d')}_"
                        f"{state_code}_"
                        f"{random.randint(1000,9999)}_"
                        f"{detail.id}"
                    )

                    detail.unique_id = unique_id
                    detail.save(update_fields=["unique_id"])

            messages.success(request, "EPR Certificate denominated successfully.")
            return redirect("denominate_epr_dashboard")

        except Exception as e:
            # Any error → rollback + user feedback
            messages.error(
                request,
                "Something went wrong while saving denomination. Please try again."
            )

            # 🔍 Optional (recommended): log real error
            print("Denomination Error:", str(e))

            return redirect("denominate_epr_certificate")
    
    
    else:
        denomination_details = (
            DenominationDetail.objects
            .filter(
                rvsf_id=rvsf_id,
                denomination_master__expiry_date__gte=today
            )
            .select_related("denomination_master")
            .values(
                "unique_id",
                "denomination_kg",
                "quantity",
                "denomination_master__denomination_date",
                "denomination_master__expiry_date",
            )
            .order_by("-denomination_master__denomination_date")
        )
        return render(request, "denominate_epr_certificate/denominate_dashboard.html", denomination_details)

def certificate_transfer_dashboard(request):

    rvsf_id = request.session.get("user_id")
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not rvsf_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not rvsf_id:
        return redirect("logoutrvsf")

    today = now()

    # -------------------------
    # FETCH DENOMINATED CERTS (MT)
    # -------------------------
    cert_denominated_mt = (
        DenominatedCertificate.objects
        .filter(
            rvsf_id=rvsf_id,
         
            expiry_date__gte=today   # only active certificates
        )
        .aggregate(total=Sum("total_certificate_value_denominated"))
        .get("total") or Decimal("0")
    )

    # -------------------------
    # CONVERT MT → KG
    # -------------------------
    certDenominated = cert_denominated_mt * Decimal("1000")

    # -------------------------
    # TRANSFERRED (for now 0)
    # -------------------------
    producer_name_subquery = Registration.objects.filter(
                            id=OuterRef("transaction__producer_id")
                        ).values("company_name")[:1]

    certTransferred = (
                    CertificateTransfer.objects
                    .filter(transaction__rvsf_id=rvsf_id)
                    .annotate(
                        total_weight=ExpressionWrapper(
                            F("denomination_detail__denomination_kg") *
                            F("denomination_detail__quantity"),
                            output_field=DecimalField()
                        ),
                        denomination_status=F("denomination_detail__status"),
                        company_name=Subquery(producer_name_subquery)
                    )
                )
    transaction_details=list(certTransferred.values())
    # total_transferred_weight = certTransferred.aggregate(
    #                                 total=Sum("total_weight")
    #                             )["total"] or 0
    total_transferred_weight = certTransferred.filter(
            transaction__status="accepted"
        ).aggregate(
            total=Sum("total_weight")
        )["total"] or 0
    remainCertAvailTransferred = certDenominated - total_transferred_weight

    context = {
        "certDenominated": certDenominated,            # KG
        "certTransferred": certTransferred,            # KG
        "remainCertAvailTransferred": remainCertAvailTransferred,
        "transaction_details": transaction_details,
        "total_transferred_weight": total_transferred_weight, 
    }
    print(context, "1111111111111111")
    return render(request, "transfer_certificate/transfer_certificate_dashboard.html", context)


def transfer_certificate(request):
    rvsf_id = request.session.get("user_id")
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not rvsf_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")

    if not rvsf_id:
        return redirect("logoutrvsf")
    rvsf_user_info = RvsfRegistration.objects.filter(id=rvsf_id).first()

    today = now()
    for_expiry_check = timezone.now().date()
    producers = Registration.objects.all()
    if request.method == "POST":

        try:
            detail_ids = request.POST.getlist("denomination_detail_id")
            producer_id = request.POST.get("producer_id")

            if not detail_ids or not producer_id:
                messages.error(request, "All fields are required.")
                return redirect("transfer_certificate")
            # Producer ID must be numeric
            if not re.match(r'^\d+$', str(producer_id)):
                messages.error(request, "Invalid producer selected.")
                return redirect("transfer_certificate")

            # Ensure producer exists
            if not Registration.objects.filter(id=producer_id).exists():
                messages.error(request, "Selected producer does not exist.")
                return redirect("transfer_certificate")

            # Validate certificate unique_id format
            for uid in detail_ids:
                # Your unique_id format:
                # rvsfId_YYYYMMDD_state_random_detailid
                if not re.match(r'^[A-Za-z0-9_]+$', uid):
                    messages.error(request, "Invalid certificate selection.")
                    return redirect("transfer_certificate")
            with transaction.atomic():

                # 🔥 1️⃣ Create one transaction (Batch Level)
                txn = CertificateTransaction.objects.create(
                    producer_id=producer_id,
                    rvsf_id=rvsf_id,
                    status="pending"
                )

                for detail_id in detail_ids:

                    detail = DenominationDetail.objects.select_related(
                        "denomination_master"
                    ).get(unique_id=detail_id, rvsf_id=rvsf_id)

                    # Expiry validation
                    if detail.denomination_master.expiry_date < timezone.now().date():
                        messages.error(
                            request,
                            f"Certificate {detail.unique_id} is expired."
                        )
                        return redirect("transfer_certificate")
                    if detail.status not in ["generated", "reverted"]:
                        messages.error(
                            request,
                            f"Certificate {detail.unique_id} is not available for transfer."
                        )
                        return redirect("transfer_certificate")
                    # 🔥 2️⃣ Create transfer row linked to transaction
                    CertificateTransfer.objects.create(
                        denomination_detail=detail,
                        transaction=txn,
                        status="pending",
                        transfer_date=now()
                    )

                    # 🔥 3️⃣ Update certificate status
                    detail.status = "under_transfer"
                    detail.save(update_fields=["status"])

            messages.success(request, "Certificates transferred successfully.")
            return redirect("transfer_certificate")

        except DenominationDetail.DoesNotExist:
            messages.error(request, "Invalid certificate selected.")
            return redirect("transfer_certificate")

        except Exception as e:
            print("Transfer Error:", str(e))
            messages.error(request, "Something went wrong during transfer.")
            return redirect("transfer_certificate")
    
    
    
    # =========================
    # GET LOGIC (DASHBOARD DATA)
    # =========================

    cert_denominated_mt = (
        DenominatedCertificate.objects
        .filter(
            rvsf_id=rvsf_id,
            expiry_date__gte=today
        )
        .aggregate(total=Sum("total_certificate_value_denominated"))
        .get("total") or Decimal("0")
    )
    certDenominated = cert_denominated_mt * Decimal("1000")

    cert_denominated_details = (
        DenominatedCertificate.objects
        .filter(
            rvsf_id=rvsf_id,
            expiry_date__gte=today
        )
        )
    certTransferred = (DenominationDetail.objects.filter(rvsf_id=rvsf_id, status="transferred", denomination_master__expiry_date__gte=today)
                        .aggregate(total=Sum( ExpressionWrapper(F("denomination_kg") * F("quantity"), output_field=DecimalField())))
                        .get("total") or Decimal("0"))
    generated_certificates = (DenominationDetail.objects.select_related("denomination_master").filter(rvsf_id=rvsf_id,
                                status__in=["generated", "reverted"], denomination_master__expiry_date__gte=today).order_by("-id"))

    remainCertAvailTransferred = certDenominated - certTransferred

    
    print(producers, "2222222222222222222")
    context = {
        "certDenominated": certDenominated,
        "certTransferred": certTransferred,
        "remainCertAvailTransferred": remainCertAvailTransferred,
        "producers": producers,
        "generated_certificates" : generated_certificates,
        "rvsf_user_info" :rvsf_user_info,
        "cert_denominated_details" : cert_denominated_details
    }
    print(certTransferred,"1111111")
    return render(
        request,
        "transfer_certificate/transfer_certificate.html",
        context
    )
    


def certificate_details(request):

    rvsf_id = request.session.get("user_id")
    user_role = request.session.get("user_role")
    is_rvsf_logged_in = request.session.get("is_rvsf_logged_in")

    if not rvsf_id or user_role != "rvsf" or not is_rvsf_logged_in:
        messages.error(request, "Unauthorized access.")
        return redirect("logoutrvsf")
    if not rvsf_id:
        return redirect("logoutrvsf")

    today = now()

    # -----------------------------
    # 🔹 Subquery for DenominationDetail
    # -----------------------------
    rvsf_name_subquery_dd = RvsfRegistration.objects.filter(
        id=OuterRef("rvsf_id")
    ).values("company_name")[:1]

    certificates_generated_list = (
        DenominationDetail.objects
        .select_related("denomination_master")
        .filter(
            rvsf_id=rvsf_id,
            denomination_master__expiry_date__gte=today,
            status__in=["generated", "reverted"]
        )
        .annotate(
            rvsf_company_name=Subquery(rvsf_name_subquery_dd)
        )
        .values(
            "id",
            "unique_id",
            "denomination_kg",
            "quantity",
            "status",
            "denomination_master__id",
            "denomination_master__expiry_date",
            "denomination_master__denomination_date",
            "rvsf_company_name"
        )
    )

    # -----------------------------
    # 🔹 Subquery for CertificateTransfer
    # -----------------------------
    producer_subquery = Registration.objects.filter(
        id=OuterRef("transaction__producer_id")
    ).values("company_name")[:1]

    rvsf_name_subquery_ct = RvsfRegistration.objects.filter(
        id=OuterRef("transaction__rvsf_id")
    ).values("company_name")[:1]

    certificates_transferred_list = (
        CertificateTransfer.objects
        .select_related(
            "denomination_detail",
            "denomination_detail__denomination_master",
            "transaction"
        )
        .filter(
            transaction__rvsf_id=rvsf_id,
            transaction__status="accepted",
            denomination_detail__status="transferred"
        )
        .annotate(
            producer_company_name=Subquery(producer_subquery),
            rvsf_company_name=Subquery(rvsf_name_subquery_ct),
            total_weight=ExpressionWrapper(
                F("denomination_detail__denomination_kg") *
                F("denomination_detail__quantity"),
                output_field=DecimalField()
            )
        )
        .values(
            "id",
            "transaction__producer_id",
            "transfer_date",
            "created_at",
            "transaction__rvsf_id",

            "denomination_detail__id",
            "denomination_detail__unique_id",
            "total_weight",
            "denomination_detail__status",
            "denomination_detail__denomination_master__expiry_date",

            "producer_company_name",
            "rvsf_company_name"
        )
    )

    context = {
        "certificates_transferred_list": certificates_transferred_list,
        "certificate_details": certificates_generated_list
    }
    print(context, "11111111")
    return render(
        request,
        "certificate_details/certificate_details.html",
        context
    )

