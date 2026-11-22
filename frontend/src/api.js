import axios from "axios";

// Cookies are HttpOnly; the browser sends them automatically on API requests.
axios.defaults.withCredentials = true;

export default axios;
