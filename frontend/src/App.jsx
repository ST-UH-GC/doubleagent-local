import HomePage from './pages/HomePage';
import { BotConfigProvider } from './contexts/BotConfigContext';
import { ChatSessionProvider } from './contexts/ChatSessionContext';

const App = () => (
  <BotConfigProvider>
    <ChatSessionProvider>
      <HomePage />
    </ChatSessionProvider>
  </BotConfigProvider>
);

export default App;
