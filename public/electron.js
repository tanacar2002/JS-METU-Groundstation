const electron = require('electron');
const path = require('path');
const url = require('url');
const { ipcMain } = require('electron');
const loadBalancer = require('electron-load-balancer');

const { app } = electron;
const { BrowserWindow } = electron;
const nativeImage = electron.nativeImage;

if (process.env.DEV) {
    const {
        default: installExtension,
        REDUX_DEVTOOLS,
        REACT_DEVELOPER_TOOLS,
    } = require('electron-devtools-installer');

    app.whenReady().then(() => {
        installExtension(REDUX_DEVTOOLS).then(name =>
            console.log(`Added Extension:  ${name}`),
        );
        installExtension(REACT_DEVELOPER_TOOLS).then(name =>
            console.log(`Added Extension:  ${name}`),
        );
    });
}

const icon = nativeImage.createFromPath(path.join(__dirname, 'app_icon.png'));
let mainWindow;

function createWindow() {
    const startUrl = process.env.DEV
        ? 'http://localhost:3000'
        : url.format({
            pathname: path.join(__dirname, '/../build/index.html'),
            protocol: 'file:',
            slashes: true,
        });
    mainWindow = new BrowserWindow({
        show: false,
        icon,
        webPreferences: {
            nodeIntegration: true,
            enableRemoteModule: true,
        },
        minWidth: 500,
        minHeight: 300,
    });
    mainWindow.maximize();
    mainWindow.show();

    mainWindow.loadURL(startUrl);
    process.env.DEV && mainWindow.webContents.openDevTools();

    mainWindow.on('closed', function () {
        loadBalancer.stopAll();
        mainWindow = null;
    });
}

app.on('ready', createWindow);

app.on('activate', () => {
    if (mainWindow === null) {
        createWindow();
    }
});

/* ----------------------------------- Custom code starts here ------------------------------------- */

// 1. Register background tasks (the keys will be used for reference later)
loadBalancer.register(
  ipcMain,
  {
    serial_loop: '/background_tasks/serial_loop.html',
    camera_loop: '/background_tasks/camera_loop.html'
  },
  { debug: false },
);

// 2. Set up eventlisteners to bounce message from background to UI 
ipcMain.on('TELEMETRY_DATA', (event, args) => {
    mainWindow.webContents.send('TELEMETRY_DATA', args);
});
ipcMain.on('CAMERA_DATA', (event, args) => {
    mainWindow.webContents.send('CAMERA_DATA', args);
});
ipcMain.on('FRAME_DATA', (event, args) => {
    mainWindow.webContents.send('FRAME_DATA', args);
});