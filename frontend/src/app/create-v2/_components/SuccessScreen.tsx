"use client";

import { motion } from "framer-motion";
import { PartyPopper, ArrowRight, Home } from "lucide-react";


interface SuccessScreenProps {
  orderId?: string | null;
}

export default function SuccessScreen({ orderId }: SuccessScreenProps) {

  const hasToken = typeof window !== "undefined" && !!localStorage.getItem("token");

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="p-6 sm:p-10 bg-white/80 backdrop-blur-xl rounded-2xl sm:rounded-3xl shadow-2xl max-w-lg mx-auto"
    >
      <div className="text-center">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", delay: 0.2 }}
          className="mx-auto mb-5 flex h-16 w-16 sm:h-20 sm:w-20 items-center justify-center rounded-full bg-green-100 text-green-600"
        >
          <PartyPopper className="h-8 w-8 sm:h-10 sm:w-10" />
        </motion.div>

        <h2 className="text-2xl sm:text-3xl font-bold text-gray-800 mb-2">
          Sipariş Alındı!
        </h2>

        {orderId && (
          <p className="text-xs text-gray-400 mb-3 font-mono">
            #{orderId.slice(0, 8).toUpperCase()}
          </p>
        )}

        <p className="text-sm sm:text-base text-gray-600 mb-6">
          Kitabınız hazırlanıyor. Siparişlerinizi hesap sayfanızdan takip edebilirsiniz.
        </p>
      </div>



      <div className="space-y-2.5">
        {hasToken && (
          <button
            type="button"
            onClick={() => (window.location.href = "/account")}
            className="w-full h-12 sm:h-14 bg-gradient-to-r from-purple-600 to-violet-600 text-white rounded-2xl font-bold text-sm sm:text-base shadow-lg shadow-purple-500/20 flex items-center justify-center gap-2 transition-transform active:scale-[0.98]"
          >
            Siparişlerimi Takip Et
            <ArrowRight className="h-4 w-4" />
          </button>
        )}
        <button
          type="button"
          onClick={() => (window.location.href = "/")}
          className="w-full h-12 sm:h-14 bg-white border-2 border-gray-200 text-gray-700 rounded-2xl font-bold text-sm sm:text-base flex items-center justify-center gap-2 transition-colors hover:bg-gray-50"
        >
          <Home className="h-4 w-4" />
          Ana Sayfaya Dön
        </button>
      </div>
    </motion.div>
  );
}
