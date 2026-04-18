:root {
    --bs-primary: #198754;
    --bs-danger: #db4437;
    --bs-secondary: #6c757d;
    --artistic-green-dark: #004d40;
    --artistic-green-light: #26a69a;
    --artistic-green-highlight: #b2dfdb;
}

.register-page-container {
    padding: 0;
}

.register-card {
    max-width: 450px;
    border-radius: 1.5rem !important;
    transition: box-shadow 0.3s ease;
}

.register-card:hover {
    box-shadow: 0 1rem 3rem rgba(0,0,0,0.175) !important;
}

.visual-showcase-static-success {
    background: linear-gradient(145deg, var(--artistic-green-dark) 0%, var(--artistic-green-light) 100%);
    position: relative;
    overflow: hidden;
}

.visual-bg-static-gradient-success {
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    background: radial-gradient(circle at 80% 20%, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0) 50%);
    z-index: 0;
}

.abstract-static-shapes-success .static-shape {
    position: absolute;
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 50%;
    filter: blur(40px);
}

.abstract-static-shapes-success .static-shape-1 {
    width: 300px; height: 300px; top: -50px; left: -100px;
}

.abstract-static-shapes-success .static-shape-2 {
    width: 200px; height: 200px; bottom: 10%; right: -50px;
}

.icon-focus-center-success {
    position: relative;
    z-index: 2;
    color: var(--artistic-green-highlight);
    text-shadow: 0 0 15px rgba(255, 255, 255, 0.7);
}

.form-control:focus {
    border-color: var(--bs-primary);
    box-shadow: 0 0 0 0.25rem rgba(25, 135, 84, 0.25);
}

.password-toggle {
    position: absolute; top: 0; right: 15px; height: 100%;
    display: flex; align-items: center; cursor: pointer;
    color: var(--bs-secondary); z-index: 10;
}

.password-toggle:hover {
    color: var(--bs-primary);
}

.register-button-effect {
    background-color: var(--bs-primary);
    border-color: var(--bs-primary);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.register-button-effect:hover {
    background-color: #157347;
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(25, 135, 84, 0.4);
}

.text-success {
    color: var(--bs-primary) !important;
}

.login-link-hover:hover {
    opacity: 0.8;
}