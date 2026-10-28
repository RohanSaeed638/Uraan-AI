import { getPortfolio } from "@/lib/server/data";

import PortfolioClient from "./PortfolioClient";

export default async function PortfolioPage() {
  const portfolio = await getPortfolio();

  return <PortfolioClient initial={portfolio} />;
}
