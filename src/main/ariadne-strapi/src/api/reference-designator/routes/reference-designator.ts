/**
 * $api router
 */

export default {
  routes: [
    {
      method: 'GET',
      path: '/reference-designator',
      handler: 'reference-designator.find',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/reference-designator/:id',
      handler: 'reference-designator.findOne',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/reference-designator',
      handler: 'reference-designator.create',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/reference-designator/:id',
      handler: 'reference-designator.update',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/reference-designator/:id',
      handler: 'reference-designator.delete',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};
