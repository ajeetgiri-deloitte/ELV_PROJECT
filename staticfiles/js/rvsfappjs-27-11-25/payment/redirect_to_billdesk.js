document.addEventListener("DOMContentLoaded", function() {
    const configEl = document.getElementById('billdeskConfig');
    const merchantId = configEl.dataset.merchantId;
    const bdOrderId = configEl.dataset.bdOrderId;
    const authToken = configEl.dataset.authToken;
    const returnUrl = configEl.dataset.returnUrl;

    const responseHandler = function (response) {
        console.log("Callback received status:", response.status);
        if (response.status === 200) {
            const encodedres = btoa(JSON.stringify(response));
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = returnUrl;

            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'transaction_response';
            input.value = encodedres;
            form.appendChild(input);
            document.body.appendChild(form);
            form.submit();
        } else if (response.status === 111) {
            // User closed the modal
            window.location.href = "/rvsf/dashboard/";
        } else {
            alert("SDK Error");
        }
    };

    const config = {
        responseHandler: responseHandler,
        flowConfig: {
            merchantId: merchantId,
            bdOrderId: bdOrderId,
            authToken: authToken,
            returnUrl: returnUrl,
            childWindow: false,
        },
        flowType: "payments"
    };

    document.getElementById("spinner").style.display = "none";
    window.loadBillDeskSdk(config);
});
