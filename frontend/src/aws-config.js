// AWS Cognito and API Gateway configuration
const awsConfig = {
  // Cognito Settings
  Auth: {
    Cognito: {
      region: 'ap-northeast-1',
      userPoolId: 'ap-northeast-1_M2sLIByIg',
      userPoolClientId: '3rklmuslmt4roe7tq0jguc9seo',
    }
  },
  
  // API Gateway Settings
  API: {
    REST: {
      'TodoAPI': {
        endpoint: 'https://av8r75bzbj.execute-api.ap-northeast-1.amazonaws.com/Prod/'.replace(/\/$/, ''),
        region: 'ap-northeast-1'
      }
    }
  }
};

export default awsConfig;
