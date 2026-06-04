import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from Transfer_Certificate.models import (
    CertificateTransaction,
    CertificateTransfer,
    CertificateTransferLog,
    DenominationDetail
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Revert expired certificate transactions after 30 minutes"

    def handle(self, *args, **kwargs):
        try:
            expiry_time = timezone.now() - timedelta(minutes=30)

            # 🔥 Find expired pending transactions
            expired_transactions = CertificateTransaction.objects.filter(
                status="pending",
                created_at__lte=expiry_time
            ).prefetch_related("transfers__denomination_detail")

            total_reverted = 0

            for txn in expired_transactions:

                with transaction.atomic():

                    # 1️⃣ Update transaction status
                    txn.status = "reverted"
                    txn.save(update_fields=["status"])

                    transfers = txn.transfers.all()

                    # 2️⃣ Update all transfers
                    CertificateTransfer.objects.filter(
                        transaction=txn
                    ).update(status="reverted")

                    # 3️⃣ Update certificates back to generated
                    DenominationDetail.objects.filter(
                        transfers__transaction=txn
                    ).update(status="generated")

                    # 4️⃣ Create logs
                    for transfer in transfers:
                        CertificateTransferLog.objects.create(
                            denomination_detail=transfer.denomination_detail,
                            producer_id=txn.producer_id,
                            transfer_date=transfer.transfer_date,
                            original_created_at=transfer.created_at,
                            action="reverted",
                            reverted_reason="Expired after 30 minutes"
                        )

                    total_reverted += 1

            logger.info(f"{total_reverted} expired transactions reverted successfully.")
            self.stdout.write(
                self.style.SUCCESS(
                    f"{total_reverted} expired transactions reverted successfully."
                )
            )

        except Exception as e:
            logger.error(f"Error in revert_expired_transactions: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f"Error occurred: {str(e)}")
            )
            
            
            