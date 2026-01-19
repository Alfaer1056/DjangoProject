// event_detail.js - Основной файл логики
document.addEventListener('DOMContentLoaded', function() {
    console.log('=== ЗАГРУЗКА СТРАНИЦЫ МЕРОПРИЯТИЯ ===');
    console.log('Event ID:', EVENT_ID);
    console.log('Current User ID:', CURRENT_USER_ID);

    // Инициализация всех компонентов
    initMoneyTab();
    initTasksTab();
    initParticipantsTab();
    initNotifications();

    // Обновляем данные при первом загрузке
    loadEventData();
});

// ============================================
// СИСТЕМА УЧЕТА ДЕНЕГ
// ============================================

function initMoneyTab() {
    // Кнопка добавления траты
    document.getElementById('addExpenseBtn').addEventListener('click', function() {
        showAddExpenseModal();
    });

    // Кнопка установки бюджета
    document.getElementById('setBudgetBtn').addEventListener('click', function() {
        setBudget();
    });

    // Переключение между равным и кастомным разделением
    document.getElementById('splitEqually').addEventListener('change', function() {
        const customSection = document.getElementById('customSplitSection');
        if (this.checked) {
            customSection.style.display = 'none';
        } else {
            customSection.style.display = 'block';
            loadParticipantsForSplit();
        }
    });

    // Сохранение траты
    document.getElementById('saveExpenseBtn').addEventListener('click', function() {
        saveExpense();
    });
}

function showAddExpenseModal() {
    // Загружаем список участников для выбора
    loadParticipantsForExpense();

    // Показываем модальное окно
    const modal = new bootstrap.Modal(document.getElementById('addExpenseModal'));
    modal.show();
}

function loadParticipantsForExpense() {
    // Здесь будет запрос к API для получения участников
    // Пока используем заглушку
    const select = document.querySelector('#addExpenseModal select[name="paid_by"]');
    select.innerHTML = `
        <option value="">Выберите участника</option>
        <option value="${CURRENT_USER_ID}">Я (Вы)</option>
        <option value="2">Алексей</option>
        <option value="3">Мария</option>
    `;
}

function loadParticipantsForSplit() {
    const container = document.getElementById('participantsSplitList');
    container.innerHTML = `
        <div class="mb-2">
            <div class="d-flex justify-content-between align-items-center">
                <span><strong>Вы (Я)</strong></span>
                <div class="input-group" style="width: 150px;">
                    <input type="number" class="form-control form-control-sm" 
                           value="0" min="0" step="0.01">
                    <span class="input-group-text">руб.</span>
                </div>
            </div>
        </div>
        <div class="mb-2">
            <div class="d-flex justify-content-between align-items-center">
                <span>Алексей</span>
                <div class="input-group" style="width: 150px;">
                    <input type="number" class="form-control form-control-sm" 
                           value="0" min="0" step="0.01">
                    <span class="input-group-text">руб.</span>
                </div>
            </div>
        </div>
    `;
}

function saveExpense() {
    const form = document.getElementById('addExpenseForm');
    const formData = new FormData(form);
    const expenseData = Object.fromEntries(formData.entries());

    // Валидация
    if (!expenseData.title || !expenseData.amount || !expenseData.paid_by) {
        Swal.fire({
            icon: 'warning',
            title: 'Заполните все поля',
            text: 'Пожалуйста, заполните все обязательные поля',
            confirmButtonText: 'Хорошо'
        });
        return;
    }

    // Показываем индикатор загрузки
    const saveBtn = document.getElementById('saveExpenseBtn');
    const originalText = saveBtn.innerHTML;
    saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
    saveBtn.disabled = true;

    // Здесь будет AJAX запрос на сохранение траты
    setTimeout(() => {
        // Имитация успешного сохранения
        Swal.fire({
            icon: 'success',
            title: 'Трата добавлена!',
            text: `Трата "${expenseData.title}" на сумму ${expenseData.amount} руб. успешно добавлена`,
            showConfirmButton: false,
            timer: 2000,
            willClose: () => {
                // Закрываем модальное окно
                bootstrap.Modal.getInstance(document.getElementById('addExpenseModal')).hide();

                // Обновляем список трат
                loadExpenses();

                // Отправляем уведомление участникам (если есть)
                sendExpenseNotification(expenseData);
            }
        });

        // Восстанавливаем кнопку
        saveBtn.innerHTML = originalText;
        saveBtn.disabled = false;
    }, 1000);
}

function setBudget() {
    Swal.fire({
        title: 'Установить бюджет',
        input: 'number',
        inputLabel: 'Общий бюджет поездки (руб)',
        inputPlaceholder: 'Введите сумму',
        showCancelButton: true,
        confirmButtonText: 'Сохранить',
        cancelButtonText: 'Отмена',
        inputValidator: (value) => {
            if (!value || value <= 0) {
                return 'Введите корректную сумму';
            }
        }
    }).then((result) => {
        if (result.isConfirmed) {
            const budget = result.value;
            document.getElementById('totalBudget').textContent = budget;

            // Сохраняем в localStorage (в реальном проекте - в базу)
            localStorage.setItem(`event_${EVENT_ID}_budget`, budget);

            // Обновляем расчеты
            updateBudgetCalculations();

            Swal.fire({
                icon: 'success',
                title: 'Бюджет сохранен!',
                text: `Бюджет установлен: ${budget} руб.`,
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: 2000
            });
        }
    });
}

// ============================================
// СИСТЕМА ЗАДАЧ
// ============================================

function initTasksTab() {
    // Кнопка добавления задачи
    document.getElementById('addTaskBtn').addEventListener('click', function() {
        showAddTaskModal();
    });

    // Фильтр задач
    document.getElementById('taskFilter').addEventListener('change', function() {
        filterTasks(this.value);
    });

    // Сохранение задачи
    document.getElementById('saveTaskBtn').addEventListener('click', function() {
        saveTask();
    });
}

function showAddTaskModal() {
    // Загружаем список участников для назначения задачи
    loadParticipantsForTask();

    // Показываем модальное окно
    const modal = new bootstrap.Modal(document.getElementById('addTaskModal'));
    modal.show();
}

function loadParticipantsForTask() {
    const select = document.querySelector('#addTaskModal select[name="assigned_to"]');
    select.innerHTML = `
        <option value="">Не назначено</option>
        <option value="${CURRENT_USER_ID}">На себя</option>
        <option value="2">Алексей</option>
        <option value="3">Мария</option>
    `;
}

function saveTask() {
    const form = document.getElementById('addTaskForm');
    const formData = new FormData(form);
    const taskData = Object.fromEntries(formData.entries());

    // Валидация
    if (!taskData.title) {
        Swal.fire({
            icon: 'warning',
            title: 'Введите название задачи',
            text: 'Пожалуйста, укажите название задачи',
            confirmButtonText: 'Хорошо'
        });
        return;
    }

    // Показываем индикатор загрузки
    const saveBtn = document.getElementById('saveTaskBtn');
    const originalText = saveBtn.innerHTML;
    saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
    saveBtn.disabled = true;

    // Здесь будет AJAX запрос на сохранение задачи
    setTimeout(() => {
        Swal.fire({
            icon: 'success',
            title: 'Задача добавлена!',
            text: `Задача "${taskData.title}" успешно создана`,
            showConfirmButton: false,
            timer: 2000,
            willClose: () => {
                // Закрываем модальное окно
                bootstrap.Modal.getInstance(document.getElementById('addTaskModal')).hide();

                // Обновляем список задач
                loadTasks();

                // Отправляем уведомление если задача назначена
                if (taskData.assigned_to) {
                    sendTaskNotification(taskData);
                }
            }
        });

        // Восстанавливаем кнопку
        saveBtn.innerHTML = originalText;
        saveBtn.disabled = false;
    }, 1000);
}

// ============================================
// УВЕДОМЛЕНИЯ
// ============================================

function initNotifications() {
    // Загружаем уведомления
    loadNotifications();

    // Настраиваем WebSocket для реальных уведомлений
    setupWebSocket();
}

function sendExpenseNotification(expenseData) {
    // Отправляем уведомление участникам о новой трате
    const notification = {
        type: 'expense',
        title: 'Новая трата',
        message: `Добавлена трата "${expenseData.title}" на сумму ${expenseData.amount} руб.`,
        event_id: EVENT_ID,
        from_user: CURRENT_USER_ID,
        timestamp: new Date().toISOString()
    };

    // Сохраняем уведомление
    saveNotification(notification);

    // Показываем уведомление текущему пользователю
    showNotification(notification);
}

function sendTaskNotification(taskData) {
    // Отправляем уведомление о новой задаче
    const notification = {
        type: 'task',
        title: 'Новая задача',
        message: `Вам назначена задача "${taskData.title}"`,
        event_id: EVENT_ID,
        from_user: CURRENT_USER_ID,
        timestamp: new Date().toISOString()
    };

    saveNotification(notification);
    showNotification(notification);
}

function showNotification(notification) {
    // Показываем toast-уведомление
    Swal.fire({
        icon: 'info',
        title: notification.title,
        text: notification.message,
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true
    });
}

// ============================================
// ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
// ============================================

function loadEventData() {
    // Загружаем все данные мероприятия
    loadExpenses();
    loadTasks();
    loadParticipants();
    loadNotifications();
    updateBudgetCalculations();
}

function loadExpenses() {
    // Заглушка - в реальном проекте будет AJAX запрос
    const expenses = [
        { id: 1, title: 'Билеты в кино', amount: 1500, paid_by: 'Вы', shares: 'Вы: 500, Алексей: 500, Мария: 500', date: '15.12.2024' },
        { id: 2, title: 'Обед в кафе', amount: 3200, paid_by: 'Алексей', shares: 'Вы: 1600, Алексей: 1600', date: '15.12.2024' }
    ];

    const tbody = document.getElementById('expensesTableBody');
    if (expenses.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted py-4">
                    <i class="bi bi-receipt fs-1"></i>
                    <p class="mb-0 mt-2">Трат пока нет</p>
                    <small>Добавьте первую трату</small>
                </td>
            </tr>
        `;
    } else {
        let html = '';
        expenses.forEach(expense => {
            html += `
                <tr>
                    <td>${expense.title}</td>
                    <td><strong>${expense.amount} руб.</strong></td>
                    <td>${expense.paid_by}</td>
                    <td><small>${expense.shares}</small></td>
                    <td><small>${expense.date}</small></td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary me-1">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger">
                            <i class="bi bi-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    }

    // Обновляем счетчик
    document.getElementById('expensesCount').textContent = expenses.length;
    document.getElementById('expensesCountBadge').textContent = expenses.length;
}

function loadTasks() {
    // Заглушка - в реальном проекте будет AJAX запрос
    const tasks = [
        { id: 1, title: 'Купить билеты', assigned_to: 'Вы', due_date: '14.12.2024', status: 'todo' },
        { id: 2, title: 'Забронировать столик', assigned_to: 'Алексей', due_date: '13.12.2024', status: 'in_progress' },
        { id: 3, title: 'Составить список', assigned_to: 'Мария', due_date: '12.12.2024', status: 'done' }
    ];

    const container = document.getElementById('tasksList');
    if (tasks.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="bi bi-card-checklist fs-1"></i>
                <p class="mb-0 mt-2">Задач пока нет</p>
                <small>Добавьте первую задачу</small>
            </div>
        `;
    } else {
        let html = '<div class="list-group list-group-flush">';
        tasks.forEach(task => {
            let statusBadge = '';
            switch(task.status) {
                case 'todo': statusBadge = '<span class="badge bg-warning">К выполнению</span>'; break;
                case 'in_progress': statusBadge = '<span class="badge bg-primary">В процессе</span>'; break;
                case 'done': statusBadge = '<span class="badge bg-success">Выполнено</span>'; break;
            }

            html += `
                <div class="list-group-item">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1">${task.title}</h6>
                            <small class="text-muted">
                                <i class="bi bi-person me-1"></i>${task.assigned_to} |
                                <i class="bi bi-calendar me-1 ms-2"></i>${task.due_date}
                            </small>
                        </div>
                        <div>
                            ${statusBadge}
                            <div class="btn-group btn-group-sm ms-2">
                                <button class="btn btn-outline-success" onclick="completeTask(${task.id})">
                                    <i class="bi bi-check"></i>
                                </button>
                                <button class="btn btn-outline-primary" onclick="editTask(${task.id})">
                                    <i class="bi bi-pencil"></i>
                                </button>
                                <button class="btn btn-outline-danger" onclick="deleteTask(${task.id})">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        container.innerHTML = html;
    }

    // Обновляем статистику
    updateTaskStatistics(tasks);
}

function updateTaskStatistics(tasks) {
    const total = tasks.length;
    const todo = tasks.filter(t => t.status === 'todo').length;
    const inProgress = tasks.filter(t => t.status === 'in_progress').length;
    const done = tasks.filter(t => t.status === 'done').length;
    const progress = total > 0 ? Math.round((done / total) * 100) : 0;

    document.getElementById('totalTasks').textContent = total;
    document.getElementById('todoTasks').textContent = todo;
    document.getElementById('inProgressTasks').textContent = inProgress;
    document.getElementById('doneTasks').textContent = done;
    document.getElementById('progressBar').style.width = `${progress}%`;
    document.getElementById('progressText').textContent = `${progress}% выполнено`;
    document.getElementById('tasksCount').textContent = total;
}

// ============================================
// ФУНКЦИИ ДЛЯ МОБИЛЬНОЙ ВЕРСИИ
// ============================================

// Адаптивность для мобильных устройств
if (window.innerWidth < 768) {
    // Мобильные улучшения
    document.querySelectorAll('.btn-group').forEach(group => {
        group.classList.add('btn-group-sm');
    });
}

// Инициализация tooltip'ов
const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
});