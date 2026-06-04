const getTrailsUrl = "{% url 'get_trails' %}";
    const roleId = {{ request.session.role_id }};

    $(document).ready(function(){
    // Search filter
    $("#searchInput").on("keyup", function() {
        const value = $(this).val().toLowerCase();
        $("table tbody tr").filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);
        });
    });

    // Modal open logic
    $('.mark-btn').click(function(){
        const userid = $(this).data('userid');
        const appno = $(this).data('appno');
        const appstatus = $(this).data('appstatus');

        $('#useridField, #useridFieldExternal').val(userid);
        $('#fetchappno, #fetchappnoExternal').val(appno);
        $('#appNoText, #appNoTextExternal').text(appno);
        $('#appstatusField').val(appstatus);

        if (appstatus == 5 && roleId == 1) {
            $('#appstatusDiv').hide();
            $('#appstatusField1').val(5);
            $('#appstatusField').prop('required', false);
        } else {
            $('#appstatusDiv').show();
            
            $('#appstatusField').prop('required', true);
        }

        fetchtrails(appno);  
    });

    $('#markModal').on('hidden.bs.modal', function () {
        $('#appstatusDiv').show();
        $('#appstatusField').prop('required', true);
    });
});

function fetchtrails(appno) {
    $.ajax({
        url: getTrailsUrl,
        data: { appno: appno },
        success: function(response) {
            const trails = response.trails;
            let trailHtml = '';
            if (trails.length > 0) {
                trails.forEach(item => {
                    trailHtml += `
                        <div style="background:#d4edda; border-left:5px solid #28a745; padding:10px; margin-bottom:8px; border-radius:5px;">
                            <strong>${item.user}</strong> 
                            <span style="color:#6c757d; font-size:12px;">(${item.designation}) – ${item.date}</span><br>
                            <em>${item.comment}</em>
                        </div>`;
                });
            } else {
                trailHtml = '<p class="text-muted">No previous actions found.</p>';
            }
            $('#trailBox').html(trailHtml);
        },
        error: function() {
            $('#trailBox').html('<p class="text-danger">Error loading previous actions.</p>');
        }
    });
}