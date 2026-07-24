/**
 * $api router
 */

export default {
  routes: [
    {
      method: 'GET',
      path: '/device',
      handler: 'device.find',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/device/:id',
      handler: 'device.findOne',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/device',
      handler: 'device.create',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/device/:id',
      handler: 'device.update',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/device/:id',
      handler: 'device.delete',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};
