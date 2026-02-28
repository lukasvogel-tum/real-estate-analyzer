import ScopeChatPanel from "@/components/ScopeChatPanel";

export default function WorkspacePage() {
  return (
    <div className="grid-2">
      <ScopeChatPanel
        title="Real Estate Portfolio Chat"
        subtitle="Shared index across all indexed real estate projects."
        defaultScope="realestate_global"
      />

      <ScopeChatPanel
        title="Global Brain Chat"
        subtitle="MVP currently uses the same shared real estate retrieval scope."
        defaultScope="global"
      />
    </div>
  );
}
