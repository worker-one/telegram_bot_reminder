from src.telegram_bot.api import telegram

def test_send_welcome(mocker):
    # Arrange
    mock_bot = mocker.MagicMock()
    mock_app = mocker.MagicMock()
    mocker.patch.object(telegram, 'bot', return_value=mock_bot)
    mocker.patch.object(telegram, 'app', return_value=mock_app)
    mock_message = mocker.MagicMock()
    mock_message.text = "test message"
    mock_message.chat.id = 12345
    mock_app.run.return_value = "test response"

    # Act
    telegram.send_welcome(mock_message)

    # Assert
    mock_app.run.assert_called_once_with("test message")
    mock_bot.reply_to.assert_called_once_with(mock_message, "test response")
