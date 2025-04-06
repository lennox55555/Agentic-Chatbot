import React from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';

// import ChatBot from './components/ChatBot';
import ChatInterface from './pages/ChatInteface/ChatInteface'

function App() {
  return <ChatInterface />
  // return (
  //   // <div className="App">
  //   //   <nav className="navbar navbar-dark bg-dark">
  //   //     <div className="container">
  //   //       <span className="navbar-brand mb-0 h1">Health & Wellness AI</span>
  //   //     </div>
  //   //   </nav>
  //   //   <main>
  //   //     <ChatBot />
  //   //   </main>
  //   //   <footer className="bg-light text-center text-muted py-3 mt-5">
  //   //     <div className="container">
  //   //       <p>Powered by AI trained on health and wellness data</p>
  //   //     </div>
  //   //   </footer>
  //   // </div>
  // );
}

export default App;