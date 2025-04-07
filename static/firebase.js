const firebaseConfig = {
    apiKey: "YOUR_API_KEY",
    authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
    projectId: "YOUR_PROJECT_ID",
    storageBucket: "YOUR_PROJECT_ID.appspot.com",
    messagingSenderId: "YOUR_SENDER_ID",
    appId: "YOUR_APP_ID"
};

const app = firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
const firestore = firebase.firestore();

if (!localStorage.getItem('isLoggedIn')) {
    // Allow access to features
} else {
    // Show modal for email input
}

document.getElementById('sendLink').addEventListener('click', function() {
    const email = document.getElementById('emailInput').value;
    const actionCodeSettings = {
        url: 'https://yourapp.com/finishSignUp?email=' + email,
        handleCodeInApp: true,
    };

    auth.sendSignInLinkToEmail(email, actionCodeSettings)
        .then(() => {
            localStorage.setItem('emailForSignIn', email);
            alert('Check your email for the magic link!');
        })
        .catch((error) => {
            console.error('Error sending email:', error);
        });
});

auth.isSignInWithEmailLink(window.location.href)
    .then((isSignIn) => {
        if (isSignIn) {
            const email = localStorage.getItem('emailForSignIn');
            auth.signInWithEmailLink(email, window.location.href)
                .then((result) => {
                    localStorage.setItem('isLoggedIn', true);
                    console.log('User signed in:', result.user.email);
                })
                .catch((error) => {
                    console.error('Error signing in:', error);
                });
        }
    });