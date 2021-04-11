import React from 'react';
import './App.css';

import Home from './Home'

// Electron related imports
const electron = window.require('electron');
const { ipcRenderer } = electron;
const loadBalancer = window.require('electron-load-balancer');

class App extends React.Component {
  constructor(props) {
    super(props);
    this.state = {};
  }

  componentDidMount(){
    // 1. Starting loops as soon as app starts
    console.log("camera loop started")
    loadBalancer.start(ipcRenderer, 'camera_loop');
    console.log("serial loop started")
    loadBalancer.start(ipcRenderer, 'serial_loop');
  }

  componentWillUnmount(){
    // 2. Shutdown loops before app stops
    loadBalancer.stop(ipcRenderer, 'camera_loop');
    loadBalancer.stop(ipcRenderer, 'serial_loop');
  }

  render() {
    return (
      <Home/>
    );
  }
}

export default App;
