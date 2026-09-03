document.addEventListener('DOMContentLoaded', function() {
    console.log("Script loaded and DOM fully loaded");

    $('#inputForm').on('submit', function(event) {
        event.preventDefault();
        var inputText = $('#ex3').val();
        $.ajax({
            url: '/submit_text',
            method: 'POST',
            data: { input_text: inputText },
            success: function(response) {
                if (response.status === 'success') {
                    console.log(data.inputText)
                }
            }
        });
    });

    $('.select-btn').on('click', function() {
        console.log("Select button clicked");
    
        var item = $(this).data('item');
        var itemExists = false;
    
        // Verifica si el ítem ya está en la lista
        $('#selected-items .list-group-item').each(function() {
            if ($(this).text().includes(item)) {
                itemExists = true;
                return false; // Sale del bucle each
            }
        });
    
        if (itemExists) {
            //alert("El ítem ya existe en la lista");
            $('#modal-messages').text(item +' já existe na lista');
            $('#Alarms').modal('show');  // Show Bootstrap modal
            console.log("Repeated activities");  // Or handle end of activities
        } else {
            var listItem = `<li class="list-group-item d-flex justify-content-between align-items-center">
                                ${item}
                                <button class="btn btn-danger remove-btn">Eliminar</button>
                            </li>`;
            $('#selected-items').append(listItem);
        }
    });
    

    $('#selected-items').on('click', '.remove-btn', function() {
        console.log("Remove button clicked");
        $(this).parent().remove();
    });

    $('#start-button').on('click', function() {
        var selectedItems = [];
        $('#selected-items li').each(function() {
            selectedItems.push($(this).text().trim());
        });
        console.log("Selected items: ", selectedItems);  // Debugging line
        if (selectedItems.length === 0){
            $('#modal-messages').text('Você não selecionou nenhuma atividade');
            $('#Alarms').modal('show');  // Show Bootstrap modal
        }
        $.ajax({
            url: '/get_activities',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ selected_items: selectedItems }),
            success: function(response) {
                if (response.status === 'success') {
                    console.log("Activities response: ", response.activities);  // Debugging line
                    if (response.activities.length > 0) {
                        // Store activities and current index in sessionStorage
                        sessionStorage.setItem('activities', JSON.stringify(response.activities));
                        sessionStorage.setItem('currentActivityIndex', 0);

                        window.location.href = '/' + response.activities[0];  // Redirect to the first activity
                    }
                }
            }
        });
    });

    function goToNextActivity() {
        var activities = JSON.parse(sessionStorage.getItem('activities'));
        var currentActivityIndex = parseInt(sessionStorage.getItem('currentActivityIndex'), 10);

        currentActivityIndex++;
        if (currentActivityIndex < activities.length) {
            sessionStorage.setItem('currentActivityIndex', currentActivityIndex);
            window.location.href = '/' + activities[currentActivityIndex];
        } else {
            // alert("Não há outras atividades. Vamos voltar ao menu principal")
            $('#endOfActivitiesModal').modal('show');  // Show Bootstrap modal
            console.log("No more activities");  // Or handle end of activities
            // window.location.href = '/';  // Redirect to the main menu
        }
    }
    
    $('#returnToMenuButton').on('click', function() {
        window.location.href = '/';  // Redirect to the main menu
    });

    $('#next-button').on('click', function() {
                goToNextActivity();
    });
});
