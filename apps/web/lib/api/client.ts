import axios from "axios";
import {createClient} from "@/lib/supabase/client";

const supabase = createClient();

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
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