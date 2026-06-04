const getTrailsUrl = "{% url 'get_trails' %}";

$(document).ready(function(){
    // Search filter
    $("#searchInput").on("keyup", function() {
        var value = $(this).val().toLowerCase();
        $("table tbody tr").filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);
        });
    });

    // Populate modal on "Mark" button click
    $('.mark-btn').click(function(){
        var userid = $(this).data('userid');
        var appno = $(this).data('appno');

        $('#useridField').val(userid);
        $('#appNoText').text(appno);
        $('#fetchappno').val(appno);

        fetchtrails(appno);  
    });
});


function fetchtrails(appno) {
    $.ajax({
        url: getTrailsUrl,  
        data: { appno: appno },
        success: function(response) {
            var trails = response.trails;
            var trailHtml = '';
            if (trails.length > 0) {
                trails.forEach(function(item){
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