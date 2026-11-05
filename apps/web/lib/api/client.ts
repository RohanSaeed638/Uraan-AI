import axios from "axios";
import { API_BASE } from "@/lib/api-base";
import {createClient} from "@/lib/supabase/client";

const supabase = createClient();

export const api = axios.create({
  baseURL: API_BASE,
});

api.interceptors.request.use(async (config) => {
  // Read the session on every request: tokens expire and are refreshed, and
  // the person may have signed out or in since this file was first loaded.
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const token = session?.access_token;

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

// After anything that changes data (finishing a lesson, a quiz, a task...),
// let the app know, so things that react to progress (the notification bell,
// which shows new achievements) can look straight away.
api.interceptors.response.use((response) => {
  if (
    typeof window !== "undefined" &&
    response.config.method &&
    response.config.method.toLowerCase() !== "get"
  ) {
    window.dispatchEvent(new Event("uraan:progress"));
  }

  return response;
});
