function printReceipt() {
    const originalContent = document.body.innerHTML;
    const receiptContent = document.getElementById("receipt").innerHTML;
    document.body.innerHTML = receiptContent;
    window.print();
    document.body.innerHTML = originalContent;
}
