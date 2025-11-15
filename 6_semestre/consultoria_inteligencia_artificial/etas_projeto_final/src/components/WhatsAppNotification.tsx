import { AlertTriangle, MessageCircle } from "lucide-react";

interface WhatsAppNotificationProps {
  message: string;
  delay: number;
}

export const WhatsAppNotification = ({ message, delay }: WhatsAppNotificationProps) => {
  return (
    <div className="bg-gradient-to-r from-[#25D366]/10 to-[#128C7E]/10 border-2 border-[#25D366]/30 rounded-lg p-4 space-y-3">
      <div className="flex items-center gap-2 text-[#075E54]">
        <MessageCircle className="w-5 h-5 fill-current" />
        <span className="font-semibold text-sm">Notificação WhatsApp</span>
      </div>
      
      <div className="bg-white rounded-lg p-3 shadow-sm relative">
        <div className="flex items-start gap-2">
          <AlertTriangle className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" />
          <p className="text-sm text-foreground">{message}</p>
        </div>
        <div className="text-xs text-muted-foreground text-right mt-2">
          {new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
        </div>
        {/* WhatsApp message tail */}
        <div className="absolute -bottom-2 left-4 w-0 h-0 border-l-8 border-l-transparent border-r-8 border-r-transparent border-t-8 border-t-white"></div>
      </div>
      
      <p className="text-xs text-muted-foreground italic">
        ℹ️ Esta é uma simulação de notificação. Em produção, seria enviada via WhatsApp.
      </p>
    </div>
  );
};
