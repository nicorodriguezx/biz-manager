function toggleNewUserForm() {
    const form = document.getElementById('new-user-form');
    form.style.display = form.style.display === 'none' ? 'block' : 'none';
}

function editUser(userId) {
    const card = document.querySelector(`div[data-id="${userId}"]`);
    const userData = {
        username: card.querySelector('.user-main h3').textContent,
        role: card.querySelector('.user-role').textContent,
        commission_rate: card.querySelector('.commission-value')?.textContent.replace('%', '') / 100 || 0
    };

    card.innerHTML = `
        <div class="user-edit-form">
            <div class="form-grid">
                <div class="form-group">
                    <label class="form-label">Usuario</label>
                    <input type="text" class="form-input username-input" value="${userData.username}" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Rol</label>
                    <select class="form-input role-input" onchange="handleRoleChange(${userId})">
                        <option value="user" ${userData.role === 'user' ? 'selected' : ''}>Usuario</option>
                        <option value="admin" ${userData.role === 'admin' ? 'selected' : ''}>Admin</option>
                    </select>
                </div>
                <div class="form-group commission-group" ${userData.role === 'admin' ? 'style="display:none"' : ''}>
                    <label class="form-label">Comisión (%)</label>
                    <input type="number" 
                           class="form-input commission-input"
                           step="0.01" 
                           min="0" 
                           max="100"
                           value="${userData.commission_rate * 100}"
                           placeholder="Comisión %">
                </div>
                <div class="form-group">
                    <label class="form-label">Contraseña</label>
                    <input type="password" 
                           class="form-input password-input" 
                           placeholder="Dejar en blanco para mantener">
                </div>
            </div>
            <div class="form-actions">
                <button onclick="saveChanges(${userId})" class="btn-text btn-save">
                    <i class="fas fa-save"></i>
                    <span class="btn-label">Guardar</span>
                </button>
                <button onclick="cancelEdit(${userId}, ${JSON.stringify(userData)})" class="btn-text btn-cancel">
                    <i class="fas fa-times"></i>
                    <span class="btn-label">Cancelar</span>
                </button>
            </div>
        </div>
    `;
}

function handleRoleChange(userId) {
    const card = document.querySelector(`div[data-id="${userId}"]`);
    const roleSelect = card.querySelector('.role-input');
    const commissionGroup = card.querySelector('.commission-group');
    
    commissionGroup.style.display = roleSelect.value === 'user' ? 'block' : 'none';
}

function saveChanges(userId) {
    const card = document.querySelector(`div[data-id="${userId}"]`);
    const data = {
        username: card.querySelector('.username-input').value,
        role: card.querySelector('.role-input').value,
    };

    if (data.role === 'user') {
        data.commission_rate = parseFloat(card.querySelector('.commission-input').value) / 100;
    }

    const password = card.querySelector('.password-input').value;
    if (password) {
        data.password = password;
    }

    fetch(`/admin/users/${userId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.reload();
        } else {
            alert(data.error || 'Error al actualizar el usuario');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al procesar la solicitud');
    });
}

function cancelEdit(userId, userData) {
    const card = document.querySelector(`div[data-id="${userId}"]`);
    card.innerHTML = `
        <div class="user-info">
            <div class="user-main">
                <h3>${userData.username}</h3>
                <span class="user-role">${userData.role}</span>
            </div>
            ${userData.role === 'user' ? `
            <div class="user-commission">
                <span class="commission-value">${(userData.commission_rate * 100).toFixed(2)}%</span>
                <span class="commission-label">comisión</span>
            </div>
            ` : ''}
        </div>
        <div class="user-actions">
            <button onclick="editUser(${userId})" class="btn-text btn-edit">
                <i class="fas fa-edit"></i>
                <span class="btn-label">Editar</span>
            </button>
            ${userId !== currentUserId ? `
            <button onclick="deleteUser(${userId})" class="btn-text btn-delete">
                <i class="fas fa-trash"></i>
                <span class="btn-label">Eliminar</span>
            </button>
            ` : ''}
        </div>
    `;
}

function deleteUser(userId) {
    if (!confirm('¿Está seguro de que desea eliminar este usuario?')) {
        return;
    }

    fetch(`/admin/users/${userId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.reload();
        } else {
            alert(data.error || 'Error al eliminar el usuario');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al eliminar el usuario');
    });
}

function handleNewRoleChange() {
    const form = document.getElementById('new-user-form');
    const roleSelect = form.querySelector('.role-input');
    const commissionGroup = form.querySelector('.commission-group');
    
    commissionGroup.style.display = roleSelect.value === 'user' ? 'block' : 'none';
}

function saveNewUser() {
    const form = document.getElementById('new-user-form');
    const data = {
        username: form.querySelector('.username-input').value,
        password: form.querySelector('.password-input').value,
        role: form.querySelector('.role-input').value,
    };

    if (!data.username || !data.password) {
        alert('Por favor complete los campos requeridos');
        return;
    }

    if (data.role === 'user') {
        const commission = form.querySelector('.commission-input').value;
        if (!commission) {
            alert('Por favor ingrese un valor de comisión');
            return;
        }
        data.commission_rate = parseFloat(commission) / 100;
    }

    fetch('/admin/users', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.reload();
        } else {
            alert(data.error || 'Error al crear el usuario');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al crear el usuario');
    });
} 