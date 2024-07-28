$(document).ready(function() {
$('#dbType').change(function() {
    if ($(this).val() === "MySQL" || $(this).val() === "PostgreSQL" || $(this).val() === "SQLite" || $(this).val() === "SQLServer") {
        $('#dbFields').show();
    } else {
        $('#dbFields').hide();
    }
});

$('#saveConversationBtn').click(function() {
    var formData = $('#addConversationForm').serialize();
    $.post('/conversation', formData, function(response) {
        if (response.success) {
            location.reload();
            window.location.href = response.redirect_url;
        } else {
            alert('Error: ' + response.message);
        }
    });
});

$('.delete-conversation').click(function() {
    var conversationId = $(this).data('id');
    if (confirm('Are you sure you want to delete this conversation?')) {
        $.ajax({
            url: '/conversation/' + conversationId,
            type: 'DELETE',
            success: function(response) {
                if (response.success) {
                    location.reload();
                } else {
                    alert('Error: ' + response.message);
                }
            }
        });
    }
});
});
