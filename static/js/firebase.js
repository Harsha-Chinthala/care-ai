import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";

// Shared Firebase configuration for frontend-only pages.
const firebaseConfig = {
    apiKey: "AIzaSyBoV-z8VnbVcsMRkLuwhsuOUd88aXVp7Hw",
    authDomain: "careai-b88db.firebaseapp.com",
    projectId: "careai-b88db",
    storageBucket: "careai-b88db.firebasestorage.app",
    messagingSenderId: "190414171649",
    appId: "1:190414171649:web:6a2925fe1364697c5f5a00"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

export { app, auth, db };
