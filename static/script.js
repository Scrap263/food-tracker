document.addEventListener('DOMContentLoaded', () => {

    // Elements
    const dateInput = document.getElementById('date-input');
    const mealList = document.getElementById('meal-list');
    const searchInput = document.getElementById('search-input');
    const searchResults = document.getElementById('search-results');
    const addMealBtn = document.getElementById('add-meal-btn');
    const saveDishBtn = document.getElementById('save-dish-btn');
    const weightInput = document.getElementById('weight-input');

    // Stats Elements
    const elStats = {
        kcal: document.getElementById('total-kcal'),
        prot: document.getElementById('total-prot'),
        fat: document.getElementById('total-fat'),
        carbs: document.getElementById('total-carbs'),
        fiber: document.getElementById('total-fiber'),
    };

    // State
    let currentDate = new Date().toISOString().split('T')[0];
    dateInput.value = currentDate;
    let selectedDish = null;

    // Load Initial Data
    loadDailyStats();

    // Listeners
    dateInput.addEventListener('change', (e) => {
        currentDate = e.target.value;
        loadDailyStats();
    });

    addMealBtn.addEventListener('click', () => {
        openModal('modal-add-meal');
        searchInput.focus();
    });

    saveDishBtn.addEventListener('click', createNewDish);

    // Live Search
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value;
        if (query.length > 1) {
            fetch(`/api/dishes?q=${query}`)
                .then(res => res.json())
                .then(data => renderSearchResults(data));
        } else {
            searchResults.style.display = 'none';
        }
    });

    // Confirm Add Meal
    document.getElementById('confirm-add-meal').addEventListener('click', () => {
        if (!selectedDish) {
            alert('Сначала выберите блюдо через поиск!');
            return;
        }
        const weight = parseFloat(weightInput.value);
        if (!weight || weight <= 0) {
            alert('Введите корректный вес!');
            return;
        }

        fetch('/api/meals', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                dish_id: selectedDish.id,
                weight_g: weight,
                date: currentDate // Send selected date
            })
        })
            .then(res => res.json())
            .then(() => {
                closeModal('modal-add-meal');
                loadDailyStats();
                weightInput.value = '';
                searchInput.value = '';
                searchResults.style.display = 'none';
                selectedDish = null;
                document.getElementById('selected-dish-info').style.display = 'none';
            });
    });

    // --- Functions ---

    function loadDailyStats() {
        console.log("Loading stats for", currentDate);
        fetch(`/api/stats?date=${currentDate}`)
            .then(res => res.json())
            .then(data => {
                // Update totals
                elStats.kcal.textContent = Math.round(data.totals.calories);
                elStats.prot.textContent = data.totals.protein;
                elStats.fat.textContent = data.totals.fat;
                elStats.carbs.textContent = data.totals.carbs;
                elStats.fiber.textContent = data.totals.fiber;

                // Update List
                if (data.meals.length === 0) {
                    mealList.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 1rem;">Пока ничего не съедено</p>';
                } else {
                    mealList.innerHTML = data.meals.map(meal => `
                        <div class="meal-item">
                            <div class="meal-info">
                                <h4>${meal.name}</h4>
                                <p>${meal.weight}г • ${meal.calories} ккал</p>
                            </div>
                            <div class="meal-values">
                                <span style="font-size: 0.8rem; color: #aaa;">Б ${meal.protein} | Ж ${meal.fat} | У ${meal.carbs}</span>
                            </div>
                        </div>
                    `).join('');
                }
            });
    }

    function renderSearchResults(dishes) {
        searchResults.innerHTML = '';
        if (dishes.length > 0) {
            searchResults.style.display = 'block';
            dishes.forEach(dish => {
                const div = document.createElement('div');
                div.className = 'search-item';
                div.innerHTML = `<b>${dish.name}</b> <small>${dish.calories} ккал</small>`;
                div.onclick = () => selectDish(dish);
                searchResults.appendChild(div);
            });
        } else {
            searchResults.style.display = 'none';
        }
    }

    function selectDish(dish) {
        selectedDish = dish;
        searchResults.style.display = 'none';
        searchInput.value = dish.name;

        const infoDiv = document.getElementById('selected-dish-info');
        infoDiv.style.display = 'block';
        document.getElementById('selected-dish-name').textContent = dish.name;
        document.getElementById('selected-dish-macros').textContent =
            `${dish.calories} ккал / 100г | Б ${dish.protein} | Ж ${dish.fat} | У ${dish.carbs}`;

        weightInput.focus();
    }

    function createNewDish() {
        const name = document.getElementById('new-name').value;
        const cal = document.getElementById('new-cal').value;
        const prot = document.getElementById('new-prot').value;
        const fat = document.getElementById('new-fat').value;
        const carbs = document.getElementById('new-carbs').value;
        const fiber = document.getElementById('new-fiber').value;

        if (!name || !cal) {
            alert('Заполните название и калорийность!');
            return;
        }

        fetch('/api/dishes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                calories: parseFloat(cal),
                protein: parseFloat(prot || 0),
                fat: parseFloat(fat || 0),
                carbs: parseFloat(carbs || 0),
                fiber: parseFloat(fiber || 0)
            })
        })
            .then(res => res.json())
            .then(newDish => {
                alert('Блюдо создано!');
                closeModal('modal-create-dish');
                // Auto Select created dish
                openModal('modal-add-meal');
                selectDish(newDish);
            });
    }
});

// Modal Helpers (Global Scope)
window.openModal = function (id) {
    document.getElementById(id).style.display = 'flex';
}
window.closeModal = function (id) {
    document.getElementById(id).style.display = 'none';
}
window.openCreateDishModal = function () {
    closeModal('modal-add-meal');
    openModal('modal-create-dish');
}
