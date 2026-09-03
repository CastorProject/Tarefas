document.addEventListener('DOMContentLoaded', (event) => {
    fetchStatus();
    // Simulación de la disminución del tiempo
    let timeLeft = 180; // 3 minutos en segundos
    const timeInterval = setInterval(() => {
        if (timeLeft > 0) {
            timeLeft--;
            document.getElementById('time-left').innerText = timeLeft;
        } else {
            clearInterval(timeInterval);
            alert('¡Se acabó el tiempo!');
        }
    }, 1000);

});

let selectedItems = {
    entertainment: [],
    food: [],
    decorations: [],
    invitations: []
};

const cost_per_activity = {
    'Palhaco': 20,
    'Peliculas': 15,
    'Musica': 10,
    'Magia': 25
};


let activities = [];
let currentActivityIndex = 0;


function fetchStatus() {
    fetch('/status')
        .then(response => response.json())
        .then(data => {
            document.getElementById('time-left').innerText = data.time_left;
            document.getElementById('budget').innerText = data.budget;
            if (data.invitations_sent) {
                disableInvitations();
            }
            if (data.decorations_bought) {
                disableDecorations();
            }
            if (data.food_prepared) {
                disableFoodPreparation();
            }
            if (data.instruction){
                disableInstruction();
            }
        });
}
// Función para enviar el archivo de audio al robot a través de Flask
function sendAudioToRobot(audioFile) {
    // Convierte la ruta al formato que el robot espera (ejemplo: static/sounds -> animals/dog)
    //const robotAudioFile = audioFile.replace('/static/', '');
    robotAudioFile = audioFile
    console.log('Enviando audio al robot:', robotAudioFile) //Debugging

    fetch('/play_audio', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ audio: robotAudioFile }),
    })
    .then(response => response.json())
    .then(data => {
        console.log('Audio enviado al robot:', data);
    })
    .catch((error) => {
        console.error('Error al enviar el audio al robot:', error);
    });
}

function openInviteModal() {
    document.getElementById('invite-modal').style.display = 'block';
}

function closeInviteModal() {
    document.getElementById('invite-modal').style.display = 'none';
}

function sendInvitations() {
    const form = document.getElementById('invite-form');
    const selectedCharacters = Array.from(form.elements['characters'])
        .filter(checkbox => checkbox.checked)
        .map(checkbox => checkbox.value);
    
    selectedItems.invitations = selectedCharacters;

    const costPerInvitation = 5;
    const totalCost = selectedCharacters.length * costPerInvitation;

    fetch('/send_invitations', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ characters: selectedCharacters })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('budget').innerText = data.budget;
            $('#scoreDisplay').text('Invitados: ' + selectedCharacters.join(', ') + '. Costo total: ' + totalCost);
            // Muestra el modal
            $('#timeUpModal').modal('show');

            if (data.invitations_sent) {
                disableInvitations();
            }
        } else {
            alert(data.message);
        }
        closeInviteModal();
    });
}

function disableInstruction() {
    document.getElementById('instruction').disabled = true;
}


function disableInvitations() {
    document.querySelector('button[onclick="openInviteModal()"]').disabled = true;
    document.getElementById('invite-modal').style.display = 'none';
}

function openDecorationModal() {
    document.getElementById('decoration-modal').style.display = 'block';
}

function closeDecorationModal() {
    document.getElementById('decoration-modal').style.display = 'none';
}

function buyDecorations() {
    const form = document.getElementById('decoration-form');
    const selectedDecorations = Array.from(form.elements['decorations'])
        .filter(checkbox => checkbox.checked)
        .map(checkbox => checkbox.value);

    selectedItems.decorations= selectedDecorations;
    
    const costPerDecoration = 10;
    const totalCost = selectedDecorations.length * costPerDecoration;

    fetch('/buy_decorations', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ decorations: selectedDecorations })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('budget').innerText = data.budget;
            $('#scoreDisplay').text('Decoraciones compradas: ' + selectedDecorations.join(', ') + '. Costo total: ' + totalCost + ' unidades.');
            // Muestra el modal
            $('#timeUpModal').modal('show');
            //alert('Decoraciones compradas: ' + selectedDecorations.join(', ') + '. Costo total: ' + totalCost + ' unidades.');
            if (data.decorations_bought) {
                disableDecorations();
            }
        } else {
            alert(data.message);
        }
        closeDecorationModal();
    });
}

function disableDecorations() {
    document.querySelector('button[onclick="openDecorationModal()"]').disabled = true;
    document.getElementById('decoration-modal').style.display = 'none';
}

function openFoodModal() {
    document.getElementById('food-modal').style.display = 'block';
}

function closeFoodModal() {
    document.getElementById('food-modal').style.display = 'none';
}

function prepareFood() {
    const form = document.getElementById('food-form');
    const selectedFoods = Array.from(form.elements['foods'])
        .filter(checkbox => checkbox.checked)
        .map(checkbox => checkbox.value);
    
    selectedItems.food=selectedFoods;

    const costPerFood = 15;
    const totalCost = selectedFoods.length * costPerFood;

    fetch('/prepare_food', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ foods: selectedFoods })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('budget').innerText = data.budget;
            $('#scoreDisplay').text('Comida preparada: ' + selectedFoods.join(', ') + '. Costo total: ' + totalCost + ' unidades.');
            // Muestra el modal
            $('#timeUpModal').modal('show');
            // alert('Comida preparada: ' + selectedFoods.join(', ') + '. Costo total: ' + totalCost + ' unidades.');
            if (data.food_prepared) {
                disableFoodPreparation();
            }
        } else {
            alert(data.message);
        }
        closeFoodModal();
    });
}

function disableFoodPreparation() {
    document.querySelector('button[onclick="openFoodModal()"]').disabled = true;
    document.getElementById('food-modal').style.display = 'none';
}

function openEntertainmentModal() {
    document.getElementById('entertainment-modal').style.display = 'block';
}

function closeEntertainmentModal() {
    document.getElementById('entertainment-modal').style.display = 'none';
}

function planEntertainment() {
    const schedule = {
        '9am-10am': document.getElementById('9am-10am').value,
        '10am-11am': document.getElementById('10am-11am').value,
        '11am-12pm': document.getElementById('11am-12pm').value,
        '12pm-1pm': document.getElementById('12pm-1pm').value,
    };

    const totalCost = Object.values(schedule).reduce((sum, activity) => {
        return sum + (cost_per_activity[activity] || 0);
    }, 0);

    if (totalCost > budget) {
        alert('No tienes suficiente presupuesto.');
        return;
    }

    selectedItems.entertainment=schedule;

    fetch('/plan_entertainment', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ activities_schedule: schedule, budget: budget })
    })

    .then(response => {
        console.log('Fetch response received:', response);
        if (!response.ok){
            throw new Error('Network response was not ok ' + response.statusText);
        }
        return response.json();
    })
    .then(data => {
        console.log('Data received:', data)
        if (data.success) {
            budget = data.budget;
            document.getElementById('budget').innerText = budget;
            $('#scoreDisplay').text('Actividades de entretenimiento planificadas. Costo total: ' + totalCost + ' unidades.');
            // Muestra el modal
            $('#timeUpModal').modal('show');
            //alert('Actividades de entretenimiento planificadas. Costo total: ' + totalCost + ' unidades.');
            if (data.success) {
                disableEntertainmentPlanning();
            }
        } else {
            alert(data.message);
        }
        closeEntertainmentModal();
    })
    .catch(error => {
        console.error('Fetch error:', error);
    });
}

function disableEntertainmentPlanning() {
    document.querySelector('button[onclick="openEntertainmentModal()"]').disabled = true;
    document.getElementById('entertainment-modal').style.display = 'none';
}

function finalizePlanning() {
    fetch('/finalize_planning', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(selectedItems)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayFinalPlan(data.plan);
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function displayFinalPlan(plan) {
    const planContainer = document.getElementById('final-plan');
    planContainer.innerHTML = ''; // Clear previous plan

    // Helper function to make an element draggable
    function makeDraggable(element) {
        element.setAttribute('draggable', true);
        element.addEventListener('dragstart', (event) => {
            event.dataTransfer.setData('text/plain', event.target.id);
        });

        // Touch events for mobile
        element.addEventListener('touchstart', touchStartHandler);
        element.addEventListener('touchmove', touchMoveHandler);
        element.addEventListener('touchend', touchEndHandler);
    }

    // Helper function to create image elements
    function createImageElement(imageUrl, altText) {
        const img = document.createElement('img');
        img.src = imageUrl;
        img.alt = altText;
        img.style.width = 'auto';
        img.style.height = 'auto';
        img.id = 'img-' + Math.random().toString(36).substr(2, 9); // Assign a unique ID
        img.style.position = 'absolute'; // Make sure the image is absolutely positioned
        makeDraggable(img);
        return img;
    }

    // Create the party scene container
    const partyScene = document.createElement('div');
    partyScene.id = 'party-scene';
    partyScene.style.width = '740px';
    partyScene.style.height = '730px';
    partyScene.style.backgroundImage = 'url("/static/images/background.png")';
    partyScene.style.backgroundSize = 'cover';
    partyScene.style.position = 'relative';
    partyScene.ondrop = drop;
    partyScene.ondragover = allowDrop;

    // Append the party scene to the plan container
    planContainer.appendChild(partyScene);

    // Display food selection
    for (const [timeSlot, foodName] of Object.entries(plan.food)) {
        const imageUrl = `/static/images/food/${foodName}.png`;
        const foodImg = createImageElement(imageUrl, 'Imagen de la comida');
        partyScene.appendChild(foodImg);
    }

    // Display decorations selection
    for (const [timeSlot, decorationName] of Object.entries(plan.decorations)) {
        const imageUrl = `/static/images/party/${decorationName}.png`;
        const decorationImg = createImageElement(imageUrl, 'Imagen de la decoracion');
        partyScene.appendChild(decorationImg);
    }

    // Display invitations selection
    for (const [timeSlot, invitationsName] of Object.entries(plan.invitations)) {
        const imageUrl = `/static/images/personajes/${invitationsName}.png`;
        const invitationImg = createImageElement(imageUrl, 'Imagen del invitado');
        partyScene.appendChild(invitationImg);
    }

    // Verifica la estructura de plan.entertainment
    console.log('Plan received', plan.entertainment);
    
    // Obtén las claves del objeto en el orden de inserción
    let timeSlots = Object.keys(plan.entertainment);

    const timeSlotOrder = [
        '9am-10am',
        '10am-11am',
        '11am-12pm',
        '12pm-1pm'
    ];

    // Filtrar las actividades para excluir las que tienen nombres vacíos
    activities = Object.entries(plan.entertainment).filter(([timeSlot, activityName]) => activityName !== '');

    // Ordenar las actividades según el orden de timeSlots en el vector
    activities.sort((a, b) => {
        const indexA = timeSlotOrder.indexOf(a[0]);
        const indexB = timeSlotOrder.indexOf(b[0]);
        return indexA - indexB;
    });

    // Mostrar la lista de actividades almacenadas
    console.log('Activities stored in order:', activities);
}

// Drag and drop functions
function allowDrop(event) {
    event.preventDefault();
}

function drop(event) {
    event.preventDefault();
    const data = event.dataTransfer.getData('text/plain');
    const img = document.getElementById(data);

    // Calculate the position within the drop area
    const dropArea = event.target;
    const rect = dropArea.getBoundingClientRect();
    const x = event.clientX - rect.left - img.width / 2;
    const y = event.clientY - rect.top - img.height / 2;

    // Set the new position of the image
    img.style.left = `${x}px`;
    img.style.top = `${y}px`;

    // Append the image to the drop area
    dropArea.appendChild(img);
}

// Touch event handlers
let selectedElement = null;
let offsetX = 0;
let offsetY = 0;

function touchStartHandler(event) {
    const touch = event.touches[0];
    selectedElement = event.target;
    const rect = selectedElement.getBoundingClientRect();
    offsetX = touch.clientX - rect.left;
    offsetY = touch.clientY - rect.top;
}

function touchMoveHandler(event) {
    if (!selectedElement) return;
    const touch = event.touches[0];
    const dropArea = document.getElementById('party-scene');
    const rect = dropArea.getBoundingClientRect();
    const x = touch.clientX - rect.left - offsetX;
    const y = touch.clientY - rect.top - offsetY;

    selectedElement.style.left = `${x}px`;
    selectedElement.style.top = `${y}px`;
}

function touchEndHandler() {
    selectedElement = null;
}

function finalizeActivities() {
    if (activities.length > 0) {
        currentActivityIndex = 0;
        showActivityModal();
    } else {
        alert('No hay actividades para mostrar.');
    }
}

function showActivityModal() {
    if (currentActivityIndex < activities.length) {
        const [timeSlot, activityName] = activities[currentActivityIndex];
        const modalBody = document.getElementById('modal-body');
        const activityImageUrl = `/static/images/activities_party/${activityName}.png`;
        const activityAudioUrl = `sounds/victory.mp3`; // Asegúrate de tener el audio en esta ruta

        // Crear el HTML para la imagen y el audio
        modalBody.innerHTML = `
            <img src="${activityImageUrl}" alt="Imagen de la actividad" style="width: 100%;" id="activityImage">
        `;

        // Obtener los elementos de la imagen y el audio
        const activityImage = document.getElementById('activityImage');

        // Añadir el evento de clic a la imagen para reproducir el audio
        if (currentActivityIndex === (activities.length -1)){
            sendAudioToRobot(activityAudioUrl);
        }
        // activityImage.addEventListener('click', () => {  
        // }
        console.log('Activity', currentActivityIndex)
        console.log('length', activities.length)

        $('#activityModal').modal('show');
    } else {
        $('#activityModal').modal('hide');
    }
}

document.getElementById('next-activity').addEventListener('click', () => {
    currentActivityIndex++;
    showActivityModal();
});

function completeTask(task) {
    // Aquí iría la lógica para completar una tarea
    alert('Tarea completada: ' + task);
    // Se debería actualizar el estado del juego en el servidor
}
