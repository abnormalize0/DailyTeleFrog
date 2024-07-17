import { axiosClient } from "../axios";

export const getPreviewArticles = (start_ts, end_ts) => {
     return axiosClient.get('/preview_articles', {
        params: {
          start_ts: start_ts,
          end_ts: end_ts
        }
      });
}