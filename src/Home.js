import React from 'react';

// Electron related imports
const electron = window.require('electron');
const { ipcRenderer } = electron;
const loadBalancer = window.require('electron-load-balancer');

class Home extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            telemetry: {

            },
            frame: {

            },
            camDevices: {
                
            }
        };
    }

    componentDidMount() {
        // Ap. Setup listener for serial loop python output (bounced from main process)
        ipcRenderer.on('TELEMETRY_DATA', (event, args) => {
            console.log(args)
            this.setState(
                {
                    ...this.state,
                    telemetry: args.data.result
                }
            )
        });

        ipcRenderer.on('FRAME_DATA', (event, args) => {
            console.log(args)
            this.setState(
                {
                    ...this.state,
                    frame: args.data.result
                }
            )
        });

        ipcRenderer.on('CAMERA_DATA', (event, args) => {
            console.log(args)
            this.setState(
                {
                    ...this.state,
                    camDevices: args.data.result
                }
            )
        });
    }

    componentWillUnmount() {
        // 4. Remove all output listeners before app shuts down
        ipcRenderer.removeAllListeners('TELEMETRY_DATA');
        ipcRenderer.removeAllListeners('CAMERA_DATA');
    }

    resetSat = () => {
        loadBalancer.sendData(
            ipcRenderer,
            'serial_loop',
            {
                command: "RESET_SATELLITE"
            }
        );
    }

    startVideoSend = () => {
        loadBalancer.sendData(
            ipcRenderer,
            'serial_loop',
            {
                command: "START_VIDEO_SEND"
            }
        );
    }

    stopVideoSend = () => {
        loadBalancer.sendData(
            ipcRenderer,
            'serial_loop',
            {
                command: "STOP_VIDEO_SEND"
            }
        );
    }

    resetVideoSend = () => {
        loadBalancer.sendData(
            ipcRenderer,
            'serial_loop',
            {
                command: "RESET_VIDEO_SEND"
            }
        );
    }

    openCamera = () => {
        loadBalancer.sendData(
            ipcRenderer,
            'camera_loop',
            {
                command: "OPEN_CAMERA",
                camID: 0
            }
        );
    }

    openSerialPort = () => {
        // 6. Sending data to serial loop (process already running)
        console.log("Serial Loop data sent")
        loadBalancer.sendData(
            ipcRenderer,
            'serial_loop',
            {
                command: "OPEN_PORT",
                port_name: "COM3",
                baudrate: 57600
            }
        );
    }

    render() {
        return (
            <div style={{
                padding: '16px'
            }}>
                <div>
                    <button onClick={this.openSerialPort}>
                        <span>Connect</span>
                    </button>
                </div>
                {
                    Object.keys(this.state.telemetry).map(key => {
                        return (
                            <div style={{
                                margin: '8px 0px 0px 0px'
                            }} key={key}>
                                {
                                    `${key} : ${this.state.telemetry[key]}`
                                }
                            </div>
                        )
                    })
                }
                <div style={{
                    margin: '16px 0px 0px 0px'
                }}>
                    <button onClick={this.resetSat}>
                        <span>Reset Satellite</span>
                    </button>
                </div>
                <div style={{
                    margin: '16px 0px 0px 0px'
                }}>
                    <button onClick={this.startVideoSend}>
                        <span>Start Sending Video</span>
                    </button>
                </div>
                <div style={{
                    margin: '16px 0px 0px 0px'
                }}>
                    <button onClick={this.stopVideoSend}>
                        <span>Stop Sending Video</span>
                    </button>
                </div>
                <div style={{
                    margin: '16px 0px 0px 0px'
                }}>
                    <button onClick={this.resetVideoSend}>
                        <span>Reset Sending Video</span>
                    </button>
                </div>
                <div style={{
                    margin: '16px 0px 0px 0px'
                }}>
                    <button onClick={this.openCamera}>
                        <span>Open Camera</span>
                    </button>
                </div>
            </div>
        )
    }
}

export default Home