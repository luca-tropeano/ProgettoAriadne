/**
 * $api router
 */

export default {
  routes: [
    {
      method: 'GET',
      path: '/material',
      handler: 'material.find',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/material/:id',
      handler: 'material.findOne',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/material',
      handler: 'material.create',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/material/:id',
      handler: 'material.update',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/material/:id',
      handler: 'material.delete',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};
