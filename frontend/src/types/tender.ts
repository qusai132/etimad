export interface Tender {
  id: number;
  reference_number: string;
  title: string;
  entity: string | null;
  activity: string | null;
  tender_type: string | null;
  publish_date: string | null;
  last_enquiry_date: string | null;
  last_offer_date: string | null;
  award_date: string | null;
  document_price: number | null;
  document_price_currency: string | null;
  tender_details: string | null;
  purpose: string | null;
  conditions: string | null;
  location: string | null;
  details_url: string | null;
  is_relevant: boolean | null;
  relevance_score: number | null;
  relevance_reason: string | null;
  matched_at: string | null;
  notification_sent: boolean;
  notification_sent_at: string | null;
  created_at: string;
  updated_at: string;
  scraped_at: string | null;
}

export interface TenderList {
  items: Tender[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface TenderFilters {
  search?: string;
  is_relevant?: boolean;
  notification_sent?: boolean;
  entity?: string;
  activity?: string;
  page: number;
  page_size: number;
}
