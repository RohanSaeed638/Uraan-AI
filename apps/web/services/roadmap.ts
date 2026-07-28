import axios from "axios";
import { createClient } from "@/lib/supabase/client";

const API = process.env.NEXT_PUBLIC_API_URL;
const supabase = createClient();

async function authHeader() {
  const {
    data: { session },
  } = await supabase.auth.getSession();

  return {
    Authorization: `Bearer ${session?.access_token}`,
  };
}

export async function generateRoadmap() {
  return axios.post(
    `${API}/roadmaps/generate`,
    {},
    {
      headers: await authHeader(),
    }
  );
}

export async function getRoadmap() {
  return axios.get(`${API}/roadmaps/current`, {
    headers: await authHeader(),
  });
}