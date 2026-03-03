import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";

export function useExclusions() {
  return useQuery({
    queryKey: ["nurse_exclusions"],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("nurse_exclusions")
        .select("nurse_id_1, nurse_id_2");
      if (error) throw error;
      return data ?? [];
    },
  });
}
