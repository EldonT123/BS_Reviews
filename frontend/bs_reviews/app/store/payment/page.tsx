"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";

type PurchaseItem = {
  id: string;
  type: "tokens" | "rank" | "cosmetic";
  name: string;
  description: string;
  price_cad?: number;
  price_tokens?: number;
  tokens_received?: number;
  rank_upgrade?: string;
};

export default function PaymentPage() {
  const router = useRouter();
  const [purchaseItem, setPurchaseItem] = useState<PurchaseItem | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  // Payment form state
  const [cardNumber, setCardNumber] = useState("");
  const [cardName, setCardName] = useState("");
  const [expiryDate, setExpiryDate] = useState("");
  const [cvv, setCvv] = useState("");
  const [billingZip, setBillingZip] = useState("");

  useEffect(() => {
    // Check if user is logged in
    const sessionId = localStorage.getItem("sessionId");
    if (!sessionId) {
      router.push("/login");
      return;
    }

    // Get pending purchase from localStorage
    const pendingPurchase = localStorage.getItem("pendingPurchase");
    if (!pendingPurchase) {
      router.push("/store");
      return;
    }

    try {
      const item = JSON.parse(pendingPurchase);
      setPurchaseItem(item);
    } catch (error) {
      console.error("Failed to parse purchase item:", error);
      router.push("/store");
    }
  }, [router]);

  const formatCardNumber = (value: string) => {
    const cleaned = value.replace(/\s/g, "");
    const formatted = cleaned.match(/.{1,4}/g)?.join(" ") || cleaned;
    return formatted.substring(0, 19); // Max 16 digits + 3 spaces
  };

  const formatExpiryDate = (value: string) => {
    const cleaned = value.replace(/\D/g, "");
    if (cleaned.length >= 2) {
      return cleaned.substring(0, 2) + "/" + cleaned.substring(2, 4);
    }
    return cleaned;
  };

  const handleCardNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatCardNumber(e.target.value);
    setCardNumber(formatted);
  };

  const handleExpiryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatExpiryDate(e.target.value);
    setExpiryDate(formatted);
  };

  const handleCvvChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, "");
    setCvv(value.substring(0, 4));
  };

  const validatePayment = (): boolean => {
    if (!cardNumber || cardNumber.replace(/\s/g, "").length < 13) {
      setError("Please enter a valid card number");
      return false;
    }
    if (!cardName || cardName.trim().length < 3) {
      setError("Please enter the cardholder name");
      return false;
    }
    if (!expiryDate || expiryDate.length !== 5) {
      setError("Please enter a valid expiry date (MM/YY)");
      return false;
    }
    if (!cvv || cvv.length < 3) {
      setError("Please enter a valid CVV");
      return false;
    }
    if (!billingZip || billingZip.length < 5) {
      setError("Please enter a valid billing ZIP code");
      return false;
    }
    return true;
  };

  const handleSubmitPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const sessionId = localStorage.getItem("sessionId");
      
      // Determine if this is a token or CAD purchase
      const isTokenPurchase = purchaseItem!.price_tokens !== undefined && purchaseItem!.price_cad === undefined;
      
      // Only validate payment info for CAD purchases
      if (!isTokenPurchase && !validatePayment()) {
        setLoading(false);
        return;
      }
      
      // Prepare payment data - conditionally include payment_method
      const paymentData: any = {
        purchase_item: purchaseItem,
      };
      
      // Only include payment_method for CAD purchases
      if (!isTokenPurchase) {
        paymentData.payment_method = {
          card_number: cardNumber.replace(/\s/g, ""),
          card_name: cardName,
          expiry_date: expiryDate,
          cvv: cvv,
          billing_zip: billingZip,
        };
      }

      // Submit payment to backend
      const response = await fetch("http://localhost:8000/api/store/process-payment", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${sessionId}`,
        },
        body: JSON.stringify(paymentData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        setError(errorData.detail || "Payment failed. Please try again.");
        setLoading(false);
        return;
      }

      // Payment successful
      setSuccess(true);
      localStorage.removeItem("pendingPurchase");

      // Redirect to success page after 2 seconds
      setTimeout(() => {
        router.push("/store?payment=success");
      }, 2000);
    } catch (error) {
      console.error("Payment error:", error);
      setError("An error occurred while processing your payment. Please try again.");
      setLoading(false);
    }
  };

  const handleCancel = () => {
    localStorage.removeItem("pendingPurchase");
    router.push("/store");
  };

  if (!purchaseItem) {
    return (
      <div className="min-h-screen bg-gray-900 text-gray-100 flex items-center justify-center">
        <p>Loading...</p>
      </div>
    );
  }

  // Fix: Use correct logic for determining purchase type
  const isCADPurchase = purchaseItem.price_cad !== undefined && purchaseItem.price_tokens === undefined;
  const isTokenPurchase = purchaseItem.price_tokens !== undefined && purchaseItem.price_cad === undefined;
  
  const amount = isCADPurchase ? purchaseItem.price_cad : purchaseItem.price_tokens;
  const currency = isCADPurchase ? "CAD" : "Tokens";

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 font-sans">
      {/* Header */}
      <header className="flex items-center justify-between px-8 py-4 bg-black/90 shadow-md sticky top-0 z-10">
        <div className="flex items-center space-x-4">
          <Link href="/">
            <Image
              src="/bs_reviews_logo.png"
              alt="BS Reviews Logo"
              width={50}
              height={20}
              className="cursor-pointer"
            />
          </Link>
        </div>
        <Link
          href="/store"
          className="text-gray-400 hover:text-gray-200 text-2xl"
        >
          ✕
        </Link>
      </header>

      {/* Main Content */}
      <section className="max-w-4xl mx-auto my-12 px-4">
        <div className="bg-gray-800 rounded-lg shadow-lg p-8">
          <h1 className="text-4xl font-bold mb-8">Complete Your Purchase</h1>

          {success ? (
            <div className="bg-green-900 text-green-200 p-6 rounded-lg text-center">
              <div className="text-5xl mb-4">✓</div>
              <h2 className="text-2xl font-bold mb-2">Payment Successful!</h2>
              <p>Redirecting you back to the store...</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Order Summary */}
              <div className="bg-gray-700 rounded-lg p-6">
                <h2 className="text-2xl font-bold mb-4">Order Summary</h2>
                <div className="space-y-4">
                  <div className="border-b border-gray-600 pb-4">
                    <h3 className="text-xl font-semibold mb-2">{purchaseItem.name}</h3>
                    <p className="text-gray-300 text-sm">{purchaseItem.description}</p>
                  </div>
                  
                  {purchaseItem.tokens_received && (
                    <div className="flex justify-between">
                      <span className="text-gray-300">Tokens:</span>
                      <span className="font-semibold">{purchaseItem.tokens_received}</span>
                    </div>
                  )}
                  
                  {purchaseItem.rank_upgrade && (
                    <div className="flex justify-between">
                      <span className="text-gray-300">New Rank:</span>
                      <span className="font-semibold capitalize">{purchaseItem.rank_upgrade}</span>
                    </div>
                  )}

                  <div className="border-t border-gray-600 pt-4 flex justify-between items-center">
                    <span className="text-xl font-bold">Total:</span>
                    <span className="text-3xl font-bold text-yellow-400">
                      {isCADPurchase ? `$${amount}` : `${amount} tokens`}
                    </span>
                  </div>
                </div>
              </div>

              {/* Payment Form */}
              <div>
                {isCADPurchase ? (
                  <form onSubmit={handleSubmitPayment} className="space-y-6">
                    <h2 className="text-2xl font-bold mb-4">Payment Information</h2>

                    {error && (
                      <div className="bg-red-900 text-red-200 p-4 rounded-lg">
                        {error}
                      </div>
                    )}

                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Card Number
                      </label>
                      <input
                        type="text"
                        value={cardNumber}
                        onChange={handleCardNumberChange}
                        placeholder="1234 5678 9012 3456"
                        className="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600 focus:border-yellow-400 focus:outline-none"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Cardholder Name
                      </label>
                      <input
                        type="text"
                        value={cardName}
                        onChange={(e) => setCardName(e.target.value)}
                        placeholder="John Doe"
                        className="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600 focus:border-yellow-400 focus:outline-none"
                        required
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium mb-2">
                          Expiry Date
                        </label>
                        <input
                          type="text"
                          value={expiryDate}
                          onChange={handleExpiryChange}
                          placeholder="MM/YY"
                          className="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600 focus:border-yellow-400 focus:outline-none"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-2">
                          CVV
                        </label>
                        <input
                          type="text"
                          value={cvv}
                          onChange={handleCvvChange}
                          placeholder="123"
                          className="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600 focus:border-yellow-400 focus:outline-none"
                          required
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Billing ZIP Code
                      </label>
                      <input
                        type="text"
                        value={billingZip}
                        onChange={(e) => setBillingZip(e.target.value)}
                        placeholder="12345"
                        className="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600 focus:border-yellow-400 focus:outline-none"
                        required
                      />
                    </div>

                    <div className="flex space-x-4">
                      <button
                        type="submit"
                        disabled={loading}
                        className="flex-1 bg-green-600 text-white font-semibold py-3 rounded hover:bg-green-700 transition disabled:bg-gray-600"
                      >
                        {loading ? "Processing..." : `Pay $${amount}`}
                      </button>
                      <button
                        type="button"
                        onClick={handleCancel}
                        disabled={loading}
                        className="flex-1 bg-gray-600 text-white font-semibold py-3 rounded hover:bg-gray-700 transition"
                      >
                        Cancel
                      </button>
                    </div>

                    <div className="text-xs text-gray-400 text-center">
                      🔒 Your payment information is secure and encrypted
                    </div>
                  </form>
                ) : (
                  <div className="space-y-6">
                    <h2 className="text-2xl font-bold mb-4">Confirm Purchase</h2>
                    <p className="text-gray-300">
                      This item will be purchased using your token balance.
                    </p>

                    {error && (
                      <div className="bg-red-900 text-red-200 p-4 rounded-lg">
                        {error}
                      </div>
                    )}

                    <div className="flex space-x-4">
                      <button
                        onClick={handleSubmitPayment}
                        disabled={loading}
                        className="flex-1 bg-green-600 text-white font-semibold py-3 rounded hover:bg-green-700 transition disabled:bg-gray-600"
                      >
                        {loading ? "Processing..." : `Confirm Purchase`}
                      </button>
                      <button
                        onClick={handleCancel}
                        disabled={loading}
                        className="flex-1 bg-gray-600 text-white font-semibold py-3 rounded hover:bg-gray-700 transition"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}