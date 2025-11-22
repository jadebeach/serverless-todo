// AWS Cognito and API Gateway configuration
const awsConfig = {
  // Cognito Settings
  Auth: {
    Cognito: {
      region: 'ap-northeast-1',
      userPoolId: 'ap-northeast-1_M2sLIByIg',        // Replace with your User Pool ID
      userPoolClientId: '3rklmuslmt4roe7tq0jguc9seo',      // Replace with your Client ID
    }
  },
  
  // API Gateway Settings
  API: {
    REST: {
      'TodoAPI': {
        endpoint: 'https://av8r75bzbj.execute-api.ap-northeast-1.amazonaws.com/Prod',  // Replace with your API URL
        region: 'ap-northeast-1'
      }
    }
  }
};

export default awsConfig;