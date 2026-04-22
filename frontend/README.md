# AirVita Frontend Dashboard

The AirVita frontend is a highly responsive, real-time React application designed to visualize environmental telemetry, present machine learning-derived health scores, and interact with the generative AI analysis system. It is built using React 18, Vite, and Tailwind CSS.

## System Architecture

> [!NOTE]
> The frontend is engineered as a Single Page Application (SPA) that heavily relies on asynchronous state updates to render real-time telemetry from the backend REST API.

### Core Technologies
- **React 18**: Manages component state, lifecycles, and UI reactivity.
- **Vite**: Provides a high-performance development server with Hot Module Replacement (HMR) and an optimized Rollup build process.
- **Tailwind CSS v4**: Utilized for rapid, utility-first styling, ensuring consistent and responsive layouts across desktop and mobile devices.
- **Lucide React**: Supplies clean, scalable vector icons used throughout the dashboard interface.
- **QRCode React**: Generates dynamic QR codes to facilitate seamless mobile device pairing.

## Setup and Configuration

### Prerequisites
Ensure Node.js 18 or newer is installed on your development system.

### Installation

Navigate to the frontend directory and install the required NPM packages:

```bash
cd frontend
npm install
```

### Execution Environments

> [!IMPORTANT]
> The Vite development server utilizes the `@vitejs/plugin-basic-ssl` plugin. This enforces HTTPS locally, which is strictly required for accessing device hardware (such as the camera for room scanning) in modern browsers.

**1. Development Server**
Start the secure Vite development server:
```bash
npm run dev
```
*The application will be securely accessible at `https://localhost:5173` or your local network IP.*

**2. Production Build**
To compile the application into static, minified assets for production deployment:
```bash
npm run build
npm run preview  # Preview the production build locally
```
*The optimized build output will be generated within the `dist/` directory.*

## User Interface Components

The interface is structured into several modular, reusable React components:

- **Primary Dashboard**: The central view aggregating the overall Room Health Score, specific sub-activity scores (Sleep, Work, Fun), and active system alerts.
- **Sensor Cards (`SensorCard.jsx`)**: Granular visualization widgets for individual telemetry metrics (e.g., Temperature, Humidity, Particulates). These cards visually indicate optimal ranges and current deviations.
- **Score Gauge (`ScoreGauge.jsx`)**: A dynamic, color-coded radial gauge representing the composite environmental health score.
- **AI Analysis Context**: An interface to trigger and display contextual recommendations sourced from the backend LLM integration, adapting to both sensor data and the visual room classification.

## Integration Protocols

> [!WARNING]
> The frontend expects the backend service to be running concurrently. If the backend is unavailable, the dashboard will display a waiting state.

### Proxy Configuration
To bypass CORS restrictions during development, `vite.config.js` is configured with a proxy interceptor. Any request sent to `/api` is automatically forwarded to the backend:

```javascript
proxy: {
  '/api': {
    target: 'http://backend:8000', // Or localhost:8000 depending on Docker vs Local execution
    changeOrigin: true,
  },
}
```
If deploying to a production environment without this proxy, ensure the backend CORS policy explicitly permits cross-origin requests from your frontend's production domain.


---

## 🔗 Related Documentation

- **[Project Overview](file:///c:/Projects/HackAugie/README.md)**: Main architecture and quick start.
- **[API Reference](file:///c:/Projects/HackAugie/API.md)**: Data schema for the telemetry endpoint.
- **[Deployment Guide](file:///c:/Projects/HackAugie/DEPLOYMENT.md)**: Docker and startup scripts.
