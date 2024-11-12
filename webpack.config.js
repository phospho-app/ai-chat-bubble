const path = require('path');
const dotenv = require('dotenv');
const webpack = require('webpack');

dotenv.config();

module.exports = {
  entry: './interface/chat-bubble.js', // path to your ChatBubble script
  output: {
    path: path.resolve(__dirname, 'component'),
    filename: 'chat-bubble.js', // output bundled file
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-react'],
          },
        },
      },
    ],
  },
  plugins: [
    new webpack.DefinePlugin({
      'process.env.SERVER_URL': JSON.stringify(process.env.SERVER_URL) || JSON.stringify('http://localhost:8080'),
    }),
  ],
  mode: 'production',
};
