import { PreviewArticlesApi } from "@/api";

export async function getPreviewArticles(start_ts, end_ts) {
  const { data } = await PreviewArticlesApi.getPreviewArticles(start_ts, end_ts);
  return data;
}