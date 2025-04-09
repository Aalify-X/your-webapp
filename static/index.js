import { initializeApp } from "https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js";
import { getAuth, signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut } from "https://www.gstatic.com/firebasejs/9.23.0/firebase-auth-compat.js";

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

// Event listeners
btnLogin.addEventListener('click', () => {
  const email = txtEmail.value;
  const password = txtPassword.value;
  
  signInWithEmailAndPassword(auth, email, password)
    .then((userCredential) => {
      showApp();
      showLoginState(userCredential.user);
    })
    .catch((error) => {
      showLoginError(error);
    });
});

btnSignup.addEventListener('click', () => {
  const email = txtEmail.value;
  const password = txtPassword.value;
  
  createUserWithEmailAndPassword(auth, email, password)
    .then((userCredential) => {
      showApp();
      showLoginState(userCredential.user);
    })
    .catch((error) => {
      showLoginError(error);
    });
});

btnLogout.addEventListener('click', () => {
  signOut(auth)
    .then(() => {
      showLoginForm();
      lblAuthState.innerHTML = '';
    })
    .catch((error) => {
      showLoginError(error);
    });
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
