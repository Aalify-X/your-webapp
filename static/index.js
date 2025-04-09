import { initializeApp } from "https://www.gstatic.com/firebasejs/9.23.0/firebase-app.js";
import { getAuth, signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/9.23.0/firebase-auth.js";

const firebaseConfig = {
  apiKey: "AIzaSyC4jmpXYuACe3KzZulDPIPHvVnNG4GWGfM",
  authDomain: "progrify-5d8f9.firebaseapp.com",
  projectId: "progrify-5d8f9",
  storageBucket: "progrify-5d8f9.appspot.com",
  messagingSenderId: "993029193028",
  appId: "1:993029193028:web:68f42d025213a98c676b11"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// DOM Elements
const txtEmail = document.querySelector('#txtEmail');
const txtPassword = document.querySelector('#txtPassword');
const btnLogin = document.querySelector('#btnLogin');
const btnSignup = document.querySelector('#btnSignup');
const btnLogout = document.querySelector('#btnLogout');
const lblAuthState = document.querySelector('#lblAuthState');
const divLoginError = document.querySelector('#divLoginError');
const lblLoginErrorMessage = document.querySelector('#lblLoginErrorMessage');

// Functions
function showLoginForm() {
  document.getElementById('login').style.display = 'block';
  document.getElementById('app').style.display = 'none';
}

function showApp() {
  document.getElementById('login').style.display = 'none';
  document.getElementById('app').style.display = 'block';
}

function hideLoginError() {
  divLoginError.style.display = 'none';
  lblLoginErrorMessage.innerHTML = '';
}

function showLoginError(error) {
  divLoginError.style.display = 'block';
  lblLoginErrorMessage.innerHTML = `Error: ${error.message}`;
}

function showLoginState(user) {
  lblAuthState.innerHTML = `You're logged in as ${user.email}`;
}

// Event Listeners
btnLogin.addEventListener('click', async () => {
  const email = txtEmail.value;
  const password = txtPassword.value;
  
  try {
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    hideLoginError();
    showApp();
    showLoginState(userCredential.user);
  } catch (error) {
    showLoginError(error);
  }
});

btnSignup.addEventListener('click', async () => {
  const email = txtEmail.value;
  const password = txtPassword.value;
  
  try {
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    hideLoginError();
    showApp();
    showLoginState(userCredential.user);
  } catch (error) {
    showLoginError(error);
  }
});

btnLogout.addEventListener('click', async () => {
  try {
    await signOut(auth);
    showLoginForm();
    lblAuthState.innerHTML = '';
  } catch (error) {
    showLoginError(error);
  }
});

// Authentication state observer
auth.onAuthStateChanged((user) => {
  if (user) {
    showApp();
    showLoginState(user);
  } else {
    showLoginForm();
    lblAuthState.innerHTML = '';
  }
});
