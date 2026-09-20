function togglePassword(id) {
    const password = document.getElementById(id);

    if (password.type === "password") {
        password.type = "text";
    } else {
        password.type = "password";
    }
}

function verifierMotDePasse() {
    const motDePasse = document.getElementById("mot_de_passe").value;
    const confirmation = document.getElementById("confirmation_mot_de_passe").value;

    if (!verifierMotDePasseFort(motDePasse)) {
        alert("Le mot de passe doit contenir au moins 8 caractères, une majuscule, une minuscule, un chiffre et un caractère spécial.");
        return false;
    }

    if (motDePasse !== confirmation) {
        alert("Les mots de passe ne correspondent pas.");
        return false;
    }

    return true;
}

// mot de passe fort

function verifierMotDePasseFort(motDePasse) {
    const longueur = motDePasse.length >= 8;
    const majuscule = /[A-Z]/.test(motDePasse);
    const minuscule = /[a-z]/.test(motDePasse);
    const chiffre = /[0-9]/.test(motDePasse);
    const special = /[^A-Za-z0-9]/.test(motDePasse);

    return longueur && majuscule && minuscule && chiffre && special;
}