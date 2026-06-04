from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from django.utils import timezone as dj_timezone

from jose import jwt

import requests
import uuid
import time
import json
import logging
from registration.models import District, State
from RvsfApp.models import *

logger = logging.getLogger("elv_logger")


class Command(BaseCommand):

    help = "Pending RVSF Payment Reconciliation Cron"

    def handle(self, *args, **kwargs):

        logger.info(
            "========== Starting Pending "
            "RVSF Payment Cron =========="
        )

        logger.info(
            "Fetching pending payments "
            "from Payment table"
        )

        pending_payments = Payment.objects.filter(
            status="payment_response_error",
            was_success=False
        ).order_by("id")

        success_count = 0
        failed_count = 0

        logger.info(
            f"Total Pending Payments Found: "
            f"{pending_payments.count()}"
        )

        for payment in pending_payments:

            try:

                logger.info(
                    "======================================"
                )

                logger.info(
                    f"Starting processing for "
                    f"Order ID: {payment.order_id}"
                )

                logger.info(
                    f"Complete Payment Object: "
                    f"{payment}"
                )

                logger.info(
                    f"Payment ID: {payment.id}"
                )

                logger.info(
                    f"Payment Owner ID: "
                    f"{payment.owner_id}"
                )

                logger.info(
                    f"Payment Current Status: "
                    f"{payment.status}"
                )

                logger.info(
                    f"Checking if payment "
                    f"is already successful"
                )

                # Skip already successful payment
                if payment.was_success:

                    logger.info(
                        f"Skipping already successful payment: "
                        f"{payment.order_id}"
                    )

                    continue

                logger.info(
                    f"Preparing BillDesk payload "
                    f"for Order ID: {payment.order_id}"
                )

                payload = {
                    "mercid": settings.BILLDESK_MERCHANT_ID,
                    "orderid": payment.order_id
                }

                logger.info(
                    f"Payload Prepared: {payload}"
                )

                logger.info(
                    "Generating Trace ID"
                )

                trace_id = uuid.uuid4().hex[:32]

                logger.info(
                    f"Trace ID Generated: {trace_id}"
                )

                logger.info(
                    "Generating Timestamp"
                )

                timestamp = str(int(time.time()))

                logger.info(
                    f"Timestamp Generated: {timestamp}"
                )

                logger.info(
                    "Preparing JWT Header"
                )

                jws_header = {
                    "alg": "HS256",
                    "clientid": settings.BILLDESK_CLIENT_ID,
                }

                logger.info(
                    f"JWT Header Prepared: "
                    f"{jws_header}"
                )

                logger.info(
                    "Preparing HTTP Headers"
                )

                http_headers = {
                    "Content-Type": "application/jose",
                    "Accept": "application/jose",
                    "BD-Traceid": trace_id,
                    "BD-Timestamp": timestamp,
                    "ClientId": settings.BILLDESK_CLIENT_ID,
                }

                logger.info(
                    f"HTTP Headers Prepared"
                )

                logger.info(
                    "Generating JWT Token"
                )

                # Encode JWT
                jws_token = jwt.encode(
                    claims=payload,
                    key=settings.BILLDESK_KEY_ID,
                    algorithm="HS256",
                    headers=jws_header
                )

                logger.info(
                    "JWT Token Generated Successfully"
                )

                logger.info(
                    f"Calling BillDesk API "
                    f"for Order ID: {payment.order_id}"
                )

                # Call BillDesk API
                response = requests.post(
                    settings.BILLDESK_RETRIEVE_PAYMENT_API_ENDPOINT,
                    headers=http_headers,
                    data=jws_token,
                    timeout=30
                )

                logger.info(
                    f"BillDesk API Status Code: "
                    f"{response.status_code}"
                )

                logger.info(
                    f"BillDesk Raw Response: "
                    f"{response.text}"
                )

                logger.info(
                    "Checking API response status"
                )

                # API Failure
                if response.status_code != 200:

                    logger.error(
                        f"BillDesk API Failed "
                        f"for Order ID: "
                        f"{payment.order_id}"
                    )

                    logger.error(
                        f"Failed Response: "
                        f"{response.text}"
                    )

                    failed_count += 1

                    continue

                logger.info(
                    "Decoding JWT Response"
                )

                # Decode Response
                decoded_data = jwt.decode(
                    token=response.text,
                    key=settings.BILLDESK_KEY_ID,
                    algorithms=["HS256"]
                )

                logger.info(
                    f"Decoded BillDesk Response: "
                    f"{json.dumps(decoded_data, indent=2)}"
                )

                logger.info(
                    "Extracting values from response"
                )

                order_id = decoded_data.get("orderid")

                txn_id = decoded_data.get("transactionid")

                status = decoded_data.get(
                    "transaction_error_type",
                    ""
                ).lower()

                amount = float(
                    decoded_data.get("amount") or 0
                )

                ru_time = decoded_data.get(
                    "transaction_date"
                )

                logger.info(
                    f"Order ID: {order_id}"
                )

                logger.info(
                    f"Transaction ID: {txn_id}"
                )

                logger.info(
                    f"Payment Status: {status}"
                )

                logger.info(
                    f"Payment Amount: {amount}"
                )

                logger.info(
                    f"Transaction Date: {ru_time}"
                )

                logger.info(
                    "Checking payment status condition"
                )

                # SUCCESS PAYMENT
                if status == "success":

                    logger.info(
                        f"SUCCESS PAYMENT received "
                        f"for Order ID: {order_id}"
                    )

                    logger.info(
                        "Starting database atomic transaction"
                    )

                    with transaction.atomic():

                        logger.info(
                            "Locking Payment row "
                            "using select_for_update"
                        )

                        # Lock payment row
                        payment = (
                            Payment.objects
                            .select_for_update()
                            .get(id=payment.id)
                        )

                        logger.info(
                            f"Payment Row Locked "
                            f"Successfully for ID: "
                            f"{payment.id}"
                        )

                        logger.info(
                            "Double checking "
                            "payment success flag"
                        )

                        # Double check
                        if payment.was_success:

                            logger.info(
                                f"Payment already processed: "
                                f"{payment.order_id}"
                            )

                            continue

                        logger.info(
                            "Preparing Payment "
                            "table update data"
                        )

                        logger.info(
                            f"Would update Payment table:\n"
                            f"txn_id={txn_id}\n"
                            f"amount_initiated="
                            f"{int(amount)}\n"
                            f"was_success=True\n"
                            f"status=success\n"
                            f"ru_date={ru_time}\n"
                            f"txn_date="
                            f"{dj_timezone.now()}"
                        )

                        # payment.txn_id = txn_id

                        # payment.amount_initiated = int(amount)

                        # payment.was_success = True

                        # payment.status = "success"

                        # payment.ru_date = ru_time

                        # payment.txn_date = dj_timezone.now()

                        # payment.log = json.dumps(
                        #     decoded_data,
                        #     indent=2
                        # )

                        # payment.save(update_fields=[
                        #     "txn_id",
                        #     "amount_initiated",
                        #     "was_success",
                        #     "status",
                        #     "ru_date",
                        #     "txn_date",
                        #     "log"
                        # ])

                        logger.info(
                            "Fetching User Details"
                        )

                        # Fetch User
                        user_id = payment.owner_id

                        logger.info(
                            f"Searching user with ID: "
                            f"{user_id}"
                        )

                        user = (
                            RvsfRegistration.objects
                            .filter(id=user_id)
                            .first()
                        )

                        logger.info(
                            f"User Query Result: {user}"
                        )

                        if not user:

                            logger.error(
                                f"User not found "
                                f"for ID: {user_id}"
                            )

                            raise Exception(
                                f"User not found for "
                                f"ID: {user_id}"
                            )

                        logger.info(
                            f"User Found Successfully"
                        )

                        logger.info(
                            f"User Username: "
                            f"{user.username}"
                        )

                        logger.info(
                            f"User Company Name: "
                            f"{user.company_name}"
                        )

                        logger.info(
                            f"User State: "
                            f"{user.state}"
                        )

                        logger.info(
                            "Fetching State Details"
                        )

                        # Fetch State
                        fetchstateid = (
                            State.objects
                            .filter(state_id=user.state)
                            .first()
                        )

                        logger.info(
                            f"State Query Result: "
                            f"{fetchstateid}"
                        )

                        stateid = (
                            fetchstateid.state_id
                            if fetchstateid else None
                        )

                        statename = (
                            fetchstateid.state_name
                            if fetchstateid else None
                        )

                        logger.info(
                            f"State ID: {stateid}"
                        )

                        logger.info(
                            f"State Name: {statename}"
                        )

                        logger.info(
                            "Checking existing "
                            "ConfirmApplication"
                        )

                        confirm_app = (
                            ConfirmApplication.objects
                            .filter(userid=user_id)
                            .first()
                        )

                        logger.info(
                            f"ConfirmApplication "
                            f"Query Result: {confirm_app}"
                        )

                        # Existing Application
                        if confirm_app:

                            logger.info(
                                f"Existing application found "
                                f"for User ID: {user_id}"
                            )

                            logger.info(
                                f"Application Number: "
                                f"{confirm_app.appno}"
                            )

                            logger.info(
                                f"Would update "
                                f"ConfirmApplication with:\n"
                                f"paymentModeStatus="
                                f"Completed\n"
                                f"transactionNo="
                                f"{order_id}{user_id}\n"
                                f"paymentstatus=1\n"
                                f"registrationfees="
                                f"{int(amount)}\n"
                                f"state_id={stateid}\n"
                                f"statename={statename}"
                            )

                            # confirm_app.paymentModeStatus = (
                            #     "Completed"
                            # )

                            # confirm_app.transactionNo = (
                            #     f"{order_id}{user_id}"
                            # )

                            # confirm_app.paymentstatus = '1'

                            # confirm_app.registrationfees = (
                            #     int(amount)
                            # )

                            # confirm_app.state_id = stateid

                            # confirm_app.statename = statename

                            # confirm_app.save(update_fields=[
                            #     "paymentModeStatus",
                            #     "transactionNo",
                            #     "paymentstatus",
                            #     "registrationfees",
                            #     "state_id",
                            #     "statename"
                            # ])

                        else:

                            logger.info(
                                f"No ConfirmApplication "
                                f"found for User ID: "
                                f"{user_id}"
                            )

                            logger.info(
                                f"Would CREATE new "
                                f"ConfirmApplication with:\n"
                                f"userid={user_id}\n"
                                f"appno="
                                f"generate_application_number()\n"
                                f"paymentModeStatus="
                                f"Completed\n"
                                f"transactionNo="
                                f"{order_id}{user_id}\n"
                                f"paymentstatus=1\n"
                                f"registrationfees="
                                f"{int(amount)}\n"
                                f"state_id={stateid}\n"
                                f"statename={statename}\n"
                                f"role_id=2\n"
                                f"marked_to_id=0"
                            )

                            # ConfirmApplication.objects.create(
                            #     userid=user_id,
                            #     appno=
                            #     generate_application_number(),
                            #     paymentModeStatus=
                            #     "Completed",
                            #     transactionNo=
                            #     f"{order_id}{user_id}",
                            #     paymentstatus='1',
                            #     registrationfees=
                            #     int(amount),
                            #     state_id=stateid,
                            #     statename=statename,
                            #     role_id=2,
                            #     marked_to_id=0
                            # )

                    success_count += 1

                    logger.info(
                        f"SUCCESS FLOW completed "
                        f"for Order ID: {order_id}"
                    )

                # FAILED PAYMENT
                else:

                    logger.warning(
                        f"FAILED PAYMENT received "
                        f"for Order ID: {order_id}"
                    )

                    logger.warning(
                        f"Would update failed payment:\n"
                        f"was_success=False\n"
                        f"status={status}"
                    )

                    # payment.was_success = False

                    # payment.status = status

                    # payment.log = json.dumps(
                    #     decoded_data,
                    #     indent=2
                    # )

                    # payment.save(update_fields=[
                    #     "was_success",
                    #     "status",
                    #     "log"
                    # ])

                    failed_count += 1

            except Exception as e:

                logger.error(
                    f"Exception occurred while "
                    f"processing Order ID: "
                    f"{payment.order_id}"
                )

                logger.error(
                    f"Error Message: {str(e)}",
                    exc_info=True
                )

                failed_count += 1

        logger.info(
            "======================================"
        )

        logger.info(
            "Pending Payment Cron Completed"
        )

        logger.info(
            f"Total Success Count: "
            f"{success_count}"
        )

        logger.info(
            f"Total Failed Count: "
            f"{failed_count}"
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Cron Completed | "
                f"Success: {success_count} | "
                f"Failed: {failed_count}"
            )
        )
        
        