import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Agent Conversation | Manual Agent',
  description: 'Interactive agent conversation powered by Manual Agent',
  openGraph: {
    title: 'Agent Conversation | Manual Agent',
    description: 'Interactive agent conversation powered by Manual Agent',
    type: 'website',
  },
};

export default function AgentsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
