document.addEventListener('DOMContentLoaded', () => {
    const profileList = document.getElementById('profile-list');
    const addProfileBtn = document.getElementById('add-profile-btn');
    const modal = document.getElementById('settings-modal');
    const closeModalBtn = document.querySelector('.close-btn');
    const changeAvatarBtn = document.getElementById('change-avatar-btn');
    const avatarInput = document.getElementById('avatar-input');
    const modalAvatar = document.getElementById('modal-avatar');
    const profileNameInput = document.getElementById('modal-profile-name');
    const saveSettingsBtn = document.getElementById('save-settings-btn');
    const deleteProfileBtn = document.getElementById('delete-profile-btn');

    let profiles = {};
    let currentProfile = null;
    let backend;

    // Função para validar o nome do perfil (sem acentos)
    const isValidProfileName = (name) => {
        return /^[a-zA-Z0-9_ ]+$/.test(name);
    };

    new QWebChannel(qt.webChannelTransport, (channel) => {
        backend = channel.objects.backend;
        loadProfiles();
    });

    async function loadProfiles() {
        try {
            const profilesData = await backend.get_profiles();
            profiles = JSON.parse(profilesData).profiles;
            renderProfiles();
        } catch (error) {
            console.error('Erro ao carregar perfis:', error);
        }
    }

    function renderProfiles() {
        profileList.innerHTML = '';
        for (const profileName in profiles) {
            const profile = profiles[profileName];
            const profileCard = document.createElement('div');
            profileCard.className = 'profile-card';
            profileCard.dataset.profileName = profileName;

            const avatar = document.createElement('div');
            avatar.className = 'profile-avatar';
            if (profile.avatar) {
                avatar.innerHTML = `<img src="${profile.avatar}" alt="${profileName}" style="width:100%; height:100%; border-radius:50%; object-fit:cover;">`;
            } else {
                avatar.textContent = profileName.charAt(0).toUpperCase();
            }

            const name = document.createElement('div');
            name.className = 'profile-name';
            name.textContent = profileName;

            const settingsBtn = document.createElement('button');
            settingsBtn.className = 'settings-btn';
            settingsBtn.innerHTML = '&#9881;';
            settingsBtn.onclick = (e) => {
                e.stopPropagation();
                openSettingsModal(profileName);
            };

            profileCard.appendChild(avatar);
            profileCard.appendChild(name);
            profileCard.appendChild(settingsBtn);
            profileCard.onclick = () => selectProfile(profileName);
            profileList.appendChild(profileCard);
        }
    }

    function openSettingsModal(profileName) {
        currentProfile = profileName;
        const profile = profiles[profileName];
        modal.style.display = 'flex';
        profileNameInput.value = profileName;
        modalAvatar.src = profile.avatar || 'placeholder.png';
    }

    closeModalBtn.onclick = () => {
        modal.style.display = 'none';
    };

    changeAvatarBtn.onclick = () => {
        avatarInput.click();
    };

    avatarInput.onchange = (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (event) => {
                modalAvatar.src = event.target.result;
            };
            reader.readAsDataURL(file);
        }
    };

    saveSettingsBtn.onclick = async () => {
        const newName = profileNameInput.value.trim();
        if (!newName) {
            alert('O nome do perfil não pode estar vazio.');
            return;
        }

        // VALIDAÇÃO: Verifica se o nome do perfil contém acentos
        if (!isValidProfileName(newName)) {
            alert('O nome do perfil não pode conter acentos ou caracteres especiais.');
            return;
        }

        const newAvatar = modalAvatar.src;

        try {
            await backend.update_profile(currentProfile, newName, newAvatar);
            modal.style.display = 'none';
            loadProfiles();
        } catch (error) {
            console.error('Erro ao salvar perfil:', error);
            alert('Erro ao salvar o perfil.');
        }
    };

    deleteProfileBtn.onclick = async () => {
        if (confirm(`Tem certeza que deseja excluir o perfil "${currentProfile}"?`)) {
            try {
                await backend.delete_profile(currentProfile);
                modal.style.display = 'none';
                loadProfiles();
            } catch (error) {
                console.error('Erro ao excluir perfil:', error);
                alert('Erro ao excluir o perfil.');
            }
        }
    };

    addProfileBtn.onclick = async () => {
        const newProfileName = prompt('Digite o nome do novo perfil (sem acentos):');
        if (newProfileName && newProfileName.trim()) {
            // VALIDAÇÃO: Verifica se o nome do perfil contém acentos
            if (!isValidProfileName(newProfileName)) {
                alert('O nome do perfil não pode conter acentos ou caracteres especiais.');
                return;
            }
            try {
                await backend.add_profile(newProfileName.trim());
                loadProfiles();
            } catch (error) {
                console.error('Erro ao adicionar perfil:', error);
                alert('Erro ao adicionar o perfil.');
            }
        }
    };

    async function selectProfile(profileName) {
        try {
            await backend.select_profile(profileName);
        } catch (error) {
            console.error('Erro ao selecionar perfil:', error);
        }
    }

    window.onclick = (event) => {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    };
});