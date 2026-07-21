import axios from "axios";
import {createClient} from "@/lib/supabase/client";

const supabase = createClient();
const {
    data: { session },
} = await supabase.auth.getSession();

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
});

api.interceptors.request.use(async (config) => {
  const token = session?.access_token;

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});