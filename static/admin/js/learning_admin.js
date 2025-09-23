function approvePattern(patternId) {
    if (confirm('Схвалити цей паттерн для додавання до бази знань?')) {
        fetch(`/admin/rag/learningpattern/${patternId}/approve/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Помилка: ' + data.error);
            }
        });
    }
}

function rejectPattern(patternId) {
    if (confirm('Відхилити цей паттерн?')) {
        fetch(`/admin/rag/learningpattern/${patternId}/reject/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Помилка: ' + data.error);
            }
        });
    }
}

function indexPattern(patternId) {
    if (confirm('Індексувати цей паттерн в базу знань?')) {
        fetch(`/admin/rag/learningpattern/${patternId}/index/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Помилка: ' + data.error);
            }
        });
    }
}
